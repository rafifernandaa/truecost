"""
SQLite Persistent Double-Entry Financial Ledger, Idempotency Store, Payment Gateway
State Machine, Webhook Deduplication & Tamper-Evident Audit Log for TrueCost Autopilot.

Implements:
- Versioned, non-destructive database migrations (`schema_migrations`)
- Integer minor-unit monetary representation (`amount_minor`, `balance_minor`) via `Decimal`
- 3 Ring-Fenced User Accounts + Counterparty Clearing Accounts:
  1. ACC_USER_CHECKING (Primary Multi-Currency Checking Account)
  2. ACC_USER_SINKING_POT (AP2 Mandate Escrow Sinking Pot)
  3. ACC_EMERGENCY_BUFFER (60-Day Protected Living Expense Reserve)
  4. ACC_EXTERNAL_INCOME_SOURCE (Counterparty Revenue / Payroll Clearing)
  5. ACC_MERCHANT_SETTLEMENT_CLEARING (Counterparty Merchant Payable Clearing)
  6. ACC_PAYMENT_GATEWAY_ESCROW (External Payment Gateway Clearing: Xendit / Midtrans)
- Immutable Double-Entry Accounting (`ledger_journals` + `ledger_entries`) with:
  - Database CHECK constraint (`total_debit_minor = total_credit_minor`)
  - SQLite BEFORE UPDATE / BEFORE DELETE triggers preventing mutation of posted entries
  - Reversing journal support for corrections/refunds
- Atomic `BEGIN IMMEDIATE` transactions for all financial writes
- Replay attack prevention (`used_nonces`) and API idempotency (`idempotency_keys`)
- External Payment Gateway transactions (`payment_transactions`), `webhook_events`,
  `reconciliation_records`, and hash-chained `audit_logs`.
"""
import hashlib
import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Generator, List, Optional, Tuple, Union

_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
_DEFAULT_DB_PATH = os.path.join(_DB_DIR, "truecost_bank.db")

MINOR_UNIT_SCALE = Decimal("100")


def to_minor_units(amount: Union[int, float, str, Decimal]) -> int:
    """
    Convert a major-unit monetary value into exact integer minor units (1 major = 100 minor).
    Never uses binary floating-point arithmetic for conversion.
    """
    if isinstance(amount, int):
        return amount * 100
    dec = Decimal(str(amount))
    minor = (dec * MINOR_UNIT_SCALE).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(minor)


def from_minor_units(amount_minor: int) -> float:
    """
    Convert integer minor units back to standard major units (2 decimal places).
    """
    dec = (Decimal(int(amount_minor)) / MINOR_UNIT_SCALE).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    return float(dec)


def from_minor_units_decimal(amount_minor: int) -> Decimal:
    """
    Convert integer minor units to exact Decimal major units.
    """
    return (Decimal(int(amount_minor)) / MINOR_UNIT_SCALE).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    target_path = db_path or os.getenv("TRUECOST_DB_PATH") or _DEFAULT_DB_PATH
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    conn = sqlite3.connect(target_path, timeout=15.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def atomic_db_transaction(db_path: Optional[str] = None) -> Generator[sqlite3.Cursor, None, None]:
    """
    Executes a block of database operations inside an atomic `BEGIN IMMEDIATE` transaction.
    Automatically rolls back all writes if any exception occurs.
    """
    conn = get_db_connection(db_path)
    conn.isolation_level = None  # Manual transaction control
    cur = conn.cursor()
    cur.execute("BEGIN IMMEDIATE")
    try:
        yield cur
        cur.execute("COMMIT")
    except Exception:
        cur.execute("ROLLBACK")
        raise
    finally:
        conn.close()


def _column_exists(cur: sqlite3.Cursor, table_name: str, column_name: str) -> bool:
    cur.execute(f"PRAGMA table_info({table_name})")
    return any(row["name"] == column_name for row in cur.fetchall())


def init_bank_db(db_path: Optional[str] = None) -> None:
    """
    Run versioned, non-destructive database migrations and seed required system accounts.
    """
    with atomic_db_transaction(db_path) as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TEXT NOT NULL
            )
            """
        )
        cur.execute("SELECT version FROM schema_migrations")
        applied_versions = {row["version"] for row in cur.fetchall()}
        now = datetime.now(timezone.utc).isoformat()

        # --- Migration v1: Base tables (backward compatible) ---
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                account_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT 'USR_DEFAULT',
                account_type TEXT NOT NULL DEFAULT 'ASSET',
                name TEXT NOT NULL,
                currency TEXT NOT NULL,
                balance REAL NOT NULL DEFAULT 0.0,
                balance_minor INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        # Non-destructive column additions if upgrading an older v1 database file
        if not _column_exists(cur, "accounts", "user_id"):
            cur.execute("ALTER TABLE accounts ADD COLUMN user_id TEXT NOT NULL DEFAULT 'USR_DEFAULT'")
        if not _column_exists(cur, "accounts", "account_type"):
            cur.execute("ALTER TABLE accounts ADD COLUMN account_type TEXT NOT NULL DEFAULT 'ASSET'")
        if not _column_exists(cur, "accounts", "balance_minor"):
            cur.execute("ALTER TABLE accounts ADD COLUMN balance_minor INTEGER NOT NULL DEFAULT 0")
            cur.execute("UPDATE accounts SET balance_minor = CAST(ROUND(balance * 100) AS INTEGER) WHERE balance_minor = 0 AND balance != 0")

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS used_nonces (
                nonce_hash TEXT PRIMARY KEY,
                mandate_id TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                tx_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT 'USR_DEFAULT',
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                amount_minor INTEGER NOT NULL DEFAULT 0,
                currency TEXT NOT NULL,
                from_account TEXT,
                to_account TEXT,
                mandate_id TEXT,
                order_id TEXT,
                journal_id TEXT,
                status TEXT NOT NULL,
                prev_tx_hash TEXT NOT NULL,
                tx_hash TEXT NOT NULL,
                metadata_json TEXT,
                timestamp TEXT NOT NULL
            )
            """
        )
        if not _column_exists(cur, "transactions", "user_id"):
            cur.execute("ALTER TABLE transactions ADD COLUMN user_id TEXT NOT NULL DEFAULT 'USR_DEFAULT'")
        if not _column_exists(cur, "transactions", "amount_minor"):
            cur.execute("ALTER TABLE transactions ADD COLUMN amount_minor INTEGER NOT NULL DEFAULT 0")
            cur.execute("UPDATE transactions SET amount_minor = CAST(ROUND(amount * 100) AS INTEGER) WHERE amount_minor = 0 AND amount != 0")
        if not _column_exists(cur, "transactions", "journal_id"):
            cur.execute("ALTER TABLE transactions ADD COLUMN journal_id TEXT")

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS executed_orders (
                order_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT 'USR_DEFAULT',
                cart_id TEXT NOT NULL,
                intent_mandate_id TEXT NOT NULL,
                item_title TEXT NOT NULL,
                merchant_name TEXT NOT NULL,
                sticker_price REAL NOT NULL,
                final_landed_cost REAL NOT NULL,
                final_landed_cost_minor INTEGER NOT NULL DEFAULT 0,
                savings_amount REAL NOT NULL DEFAULT 0.0,
                currency TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                effective_apr REAL NOT NULL,
                disposable_card_id TEXT NOT NULL,
                debit_source TEXT NOT NULL,
                status TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
            """
        )
        if not _column_exists(cur, "executed_orders", "user_id"):
            cur.execute("ALTER TABLE executed_orders ADD COLUMN user_id TEXT NOT NULL DEFAULT 'USR_DEFAULT'")
        if not _column_exists(cur, "executed_orders", "final_landed_cost_minor"):
            cur.execute("ALTER TABLE executed_orders ADD COLUMN final_landed_cost_minor INTEGER NOT NULL DEFAULT 0")

        if 1 not in applied_versions:
            cur.execute(
                "INSERT INTO schema_migrations (version, name, applied_at) VALUES (?, ?, ?)",
                (1, "v1_core_bank_tables", now),
            )

        # --- Migration v2: Users & Immutable Double-Entry Ledger ---
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                public_key_hex TEXT,
                role TEXT NOT NULL DEFAULT 'STUDENT_USER',
                status TEXT NOT NULL DEFAULT 'ACTIVE',
                created_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            INSERT OR IGNORE INTO users (user_id, email, full_name, role, status, created_at)
            VALUES ('USR_DEFAULT', 'rafif@student.truecost.id', 'Rafif (Primary Account Holder)', 'STUDENT_USER', 'ACTIVE', ?)
            """,
            (now,),
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS ledger_journals (
                journal_id TEXT PRIMARY KEY,
                tx_id TEXT UNIQUE,
                user_id TEXT NOT NULL DEFAULT 'USR_DEFAULT',
                entry_type TEXT NOT NULL,
                description TEXT NOT NULL,
                currency TEXT NOT NULL,
                total_debit_minor INTEGER NOT NULL,
                total_credit_minor INTEGER NOT NULL,
                is_reversal INTEGER NOT NULL DEFAULT 0,
                reverses_journal_id TEXT,
                prev_journal_hash TEXT NOT NULL,
                journal_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                CHECK (total_debit_minor = total_credit_minor AND total_debit_minor > 0)
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS ledger_entries (
                entry_id TEXT PRIMARY KEY,
                journal_id TEXT NOT NULL,
                account_id TEXT NOT NULL,
                direction TEXT NOT NULL CHECK (direction IN ('DEBIT', 'CREDIT')),
                amount_minor INTEGER NOT NULL CHECK (amount_minor > 0),
                currency TEXT NOT NULL,
                balance_after_minor INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (journal_id) REFERENCES ledger_journals(journal_id),
                FOREIGN KEY (account_id) REFERENCES accounts(account_id)
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_ledger_entries_journal ON ledger_entries(journal_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_ledger_entries_account ON ledger_entries(account_id)")

        # Enforce immutability of posted ledger entries at the database trigger level
        cur.execute(
            """
            CREATE TRIGGER IF NOT EXISTS trg_ledger_entries_immutable_update
            BEFORE UPDATE ON ledger_entries
            BEGIN
                SELECT RAISE(ABORT, 'IMMUTABLE_LEDGER_VIOLATION: Posted ledger entries cannot be modified. Post a reversing journal entry instead.');
            END;
            """
        )
        cur.execute(
            """
            CREATE TRIGGER IF NOT EXISTS trg_ledger_entries_immutable_delete
            BEFORE DELETE ON ledger_entries
            BEGIN
                SELECT RAISE(ABORT, 'IMMUTABLE_LEDGER_VIOLATION: Posted ledger entries cannot be deleted. Post a reversing journal entry instead.');
            END;
            """
        )

        if 2 not in applied_versions:
            cur.execute(
                "INSERT INTO schema_migrations (version, name, applied_at) VALUES (?, ?, ?)",
                (2, "v2_double_entry_ledger_and_immutability_triggers", now),
            )

        # --- Migration v3: Mandates, Cards, Idempotency, Payment Gateway, Webhooks, Reconciliation, Audit ---
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS intent_mandates_store (
                mandate_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT 'USR_DEFAULT',
                user_public_key TEXT NOT NULL,
                item_query TEXT NOT NULL,
                max_budget_minor INTEGER NOT NULL,
                currency TEXT NOT NULL,
                mandate_json TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'ACTIVE',
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS disposable_cards_store (
                card_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT 'USR_DEFAULT',
                cart_id TEXT NOT NULL,
                masked_pan TEXT NOT NULL,
                currency TEXT NOT NULL,
                spending_limit_minor INTEGER NOT NULL,
                merchant_id TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS idempotency_keys (
                idempotency_key TEXT NOT NULL,
                user_id TEXT NOT NULL DEFAULT 'USR_DEFAULT',
                endpoint TEXT NOT NULL,
                request_hash TEXT NOT NULL,
                response_status INTEGER NOT NULL,
                response_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                PRIMARY KEY (idempotency_key, user_id, endpoint)
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS payment_transactions (
                payment_id TEXT PRIMARY KEY,
                order_id TEXT,
                mandate_id TEXT,
                user_id TEXT NOT NULL DEFAULT 'USR_DEFAULT',
                provider TEXT NOT NULL,
                provider_reference TEXT UNIQUE NOT NULL,
                payment_method TEXT NOT NULL,
                merchant_name TEXT NOT NULL,
                item_title TEXT NOT NULL,
                amount_minor INTEGER NOT NULL CHECK (amount_minor > 0),
                currency TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('PENDING', 'PAID', 'FAILED', 'EXPIRED', 'CANCELLED', 'REFUNDED')),
                checkout_url TEXT,
                qr_string TEXT,
                va_number TEXT,
                idempotency_key TEXT UNIQUE,
                journal_id TEXT,
                reversal_journal_id TEXT,
                metadata_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                settled_at TEXT
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_payment_tx_user ON payment_transactions(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_payment_tx_status ON payment_transactions(status)")

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS webhook_events (
                event_id TEXT PRIMARY KEY,
                provider TEXT NOT NULL,
                provider_event_id TEXT NOT NULL,
                payment_id TEXT,
                signature_verified INTEGER NOT NULL,
                payload_hash TEXT NOT NULL,
                raw_payload_json TEXT NOT NULL,
                processing_status TEXT NOT NULL CHECK (processing_status IN ('PROCESSED', 'DUPLICATE_IGNORED', 'REJECTED_SIGNATURE', 'FAILED')),
                error_message TEXT,
                received_at TEXT NOT NULL,
                processed_at TEXT,
                UNIQUE (provider, provider_event_id)
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS reconciliation_records (
                recon_id TEXT PRIMARY KEY,
                run_timestamp TEXT NOT NULL,
                total_checked INTEGER NOT NULL,
                matched_count INTEGER NOT NULL,
                mismatched_count INTEGER NOT NULL,
                auto_healed_count INTEGER NOT NULL,
                discrepancies_json TEXT NOT NULL,
                status TEXT NOT NULL
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                audit_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT,
                status TEXT NOT NULL,
                ip_address TEXT,
                details_json TEXT,
                prev_audit_hash TEXT NOT NULL,
                audit_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TRIGGER IF NOT EXISTS trg_audit_logs_immutable_update
            BEFORE UPDATE ON audit_logs
            BEGIN
                SELECT RAISE(ABORT, 'IMMUTABLE_AUDIT_VIOLATION: Audit log entries cannot be modified.');
            END;
            """
        )
        cur.execute(
            """
            CREATE TRIGGER IF NOT EXISTS trg_audit_logs_immutable_delete
            BEFORE DELETE ON audit_logs
            BEGIN
                SELECT RAISE(ABORT, 'IMMUTABLE_AUDIT_VIOLATION: Audit log entries cannot be deleted.');
            END;
            """
        )

        if 3 not in applied_versions:
            cur.execute(
                "INSERT INTO schema_migrations (version, name, applied_at) VALUES (?, ?, ?)",
                (3, "v3_idempotency_payments_webhooks_reconciliation_audit", now),
            )

        # Ensure default user & system counterparty accounts exist without overwriting existing balances
        _seed_accounts_if_missing(cur, now)


def _seed_accounts_if_missing(cur: sqlite3.Cursor, now: str) -> None:
    default_accounts = [
        (
            "ACC_USER_CHECKING",
            "USR_DEFAULT",
            "ASSET",
            "Primary Student Checking Account",
            "IDR",
            25000000.0,
            to_minor_units(25000000),
            "ACTIVE",
            now,
        ),
        (
            "ACC_USER_SINKING_POT",
            "USR_DEFAULT",
            "ASSET",
            "Laptop Purchase Sinking Fund Pot",
            "IDR",
            0.0,
            0,
            "ACTIVE",
            now,
        ),
        (
            "ACC_EMERGENCY_BUFFER",
            "USR_DEFAULT",
            "ASSET",
            "60-Day Protected Living Buffer",
            "IDR",
            10000000.0,
            to_minor_units(10000000),
            "RINGFENCED_PROTECTED",
            now,
        ),
        (
            "ACC_EXTERNAL_INCOME_SOURCE",
            "SYSTEM",
            "REVENUE",
            "External Payroll & Allowance Clearing",
            "IDR",
            0.0,
            0,
            "SYSTEM_CLEARING",
            now,
        ),
        (
            "ACC_MERCHANT_SETTLEMENT_CLEARING",
            "SYSTEM",
            "EXPENSE",
            "Merchant Settlement Payable Clearing",
            "IDR",
            0.0,
            0,
            "SYSTEM_CLEARING",
            now,
        ),
        (
            "ACC_PAYMENT_GATEWAY_ESCROW",
            "SYSTEM",
            "ASSET",
            "Payment Gateway Escrow Clearing (Xendit/Midtrans)",
            "IDR",
            0.0,
            0,
            "SYSTEM_CLEARING",
            now,
        ),
    ]
    cur.executemany(
        """
        INSERT OR IGNORE INTO accounts (
            account_id, user_id, account_type, name, currency, balance, balance_minor, status, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        default_accounts,
    )


def compute_tx_chain_hash(prev_hash: str, tx_payload: Dict[str, Any]) -> str:
    canonical = json.dumps(tx_payload, sort_keys=True, default=str)
    return hashlib.sha256(f"{prev_hash}|{canonical}".encode("utf-8")).hexdigest()


def post_double_entry_journal(
    cur: sqlite3.Cursor,
    *,
    tx_id: str,
    user_id: str,
    entry_type: str,
    description: str,
    currency: str,
    postings: List[Tuple[str, str, int]],
    is_reversal: bool = False,
    reverses_journal_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Posts a balanced double-entry accounting journal inside an active atomic transaction cursor.
    `postings` is a list of `(account_id, direction, amount_minor)` where `direction` is 'DEBIT' or 'CREDIT'.

    Accounting convention for user asset accounts & system clearing accounts:
    - For ASSET accounts (`ACC_USER_CHECKING`, `ACC_USER_SINKING_POT`, `ACC_EMERGENCY_BUFFER`):
      Wait: in our user-facing banking model, crediting an account increases its balance and debiting decreases it,
      OR in standard double-entry:
      Every transfer from `source_account` to `dest_account` has:
      - DEBIT `source_account` (or outflow) / CREDIT `dest_account` (or inflow) such that
        total `DEBIT` == total `CREDIT`!
      Let's make the balance update explicit and unambiguous:
      In each posting `(account_id, direction, amount_minor)`:
      - `DEBIT` reduces the source account balance (`-amount_minor`)
      - `CREDIT` increases the destination account balance (`+amount_minor`)
      - `SUM(DEBIT amount_minor) == SUM(CREDIT amount_minor)` is strictly verified in Python AND by SQLite CHECK constraint!
    """
    if not postings:
        raise ValueError("Double-entry journal requires at least two postings.")

    total_debit = sum(amt for _, direction, amt in postings if direction == "DEBIT")
    total_credit = sum(amt for _, direction, amt in postings if direction == "CREDIT")

    if total_debit <= 0 or total_debit != total_credit:
        raise ValueError(
            f"UNBALANCED_JOURNAL: total_debit_minor ({total_debit}) != total_credit_minor ({total_credit})"
        )

    now = datetime.now(timezone.utc).isoformat()
    journal_id = f"JRN_{uuid.uuid4().hex[:12].upper()}"

    cur.execute("SELECT journal_hash FROM ledger_journals ORDER BY created_at DESC, rowid DESC LIMIT 1")
    last_row = cur.fetchone()
    prev_hash = last_row["journal_hash"] if last_row else "0" * 64

    journal_payload = {
        "journal_id": journal_id,
        "tx_id": tx_id,
        "entry_type": entry_type,
        "total_debit_minor": total_debit,
        "total_credit_minor": total_credit,
        "postings": postings,
        "created_at": now,
    }
    journal_hash = compute_tx_chain_hash(prev_hash, journal_payload)

    cur.execute(
        """
        INSERT INTO ledger_journals (
            journal_id, tx_id, user_id, entry_type, description, currency,
            total_debit_minor, total_credit_minor, is_reversal, reverses_journal_id,
            prev_journal_hash, journal_hash, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            journal_id,
            tx_id,
            user_id,
            entry_type,
            description,
            currency,
            total_debit,
            total_credit,
            1 if is_reversal else 0,
            reverses_journal_id,
            prev_hash,
            journal_hash,
            now,
        ),
    )

    entries_created: List[Dict[str, Any]] = []
    for account_id, direction, amount_minor in postings:
        if amount_minor <= 0:
            raise ValueError(f"Posting amount_minor must be positive, got {amount_minor}")

        cur.execute("SELECT balance_minor, account_type, status FROM accounts WHERE account_id = ?", (account_id,))
        acc_row = cur.fetchone()
        if not acc_row:
            raise ValueError(f"Ledger account '{account_id}' does not exist.")

        current_minor = int(acc_row["balance_minor"])
        delta = -amount_minor if direction == "DEBIT" else amount_minor
        new_minor = current_minor + delta

        # User-owned ringfenced or asset accounts may never go negative
        if acc_row["status"] != "SYSTEM_CLEARING" and new_minor < 0:
            raise ValueError(
                f"INSUFFICIENT_FUNDS: Account {account_id} has {from_minor_units(current_minor):,.2f} {currency}, "
                f"cannot debit {from_minor_units(amount_minor):,.2f} {currency}."
            )

        new_major = from_minor_units(new_minor)
        cur.execute(
            "UPDATE accounts SET balance_minor = ?, balance = ?, updated_at = ? WHERE account_id = ?",
            (new_minor, new_major, now, account_id),
        )

        entry_id = f"LGE_{uuid.uuid4().hex[:12].upper()}"
        cur.execute(
            """
            INSERT INTO ledger_entries (
                entry_id, journal_id, account_id, direction, amount_minor,
                currency, balance_after_minor, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry_id,
                journal_id,
                account_id,
                direction,
                amount_minor,
                currency,
                new_minor,
                now,
            ),
        )
        entries_created.append(
            {
                "entry_id": entry_id,
                "journal_id": journal_id,
                "account_id": account_id,
                "direction": direction,
                "amount_minor": amount_minor,
                "amount": from_minor_units(amount_minor),
                "currency": currency,
                "balance_after_minor": new_minor,
                "balance_after": new_major,
            }
        )

    return {
        "journal_id": journal_id,
        "tx_id": tx_id,
        "total_debit_minor": total_debit,
        "total_credit_minor": total_credit,
        "journal_hash": journal_hash[:16],
        "entries": entries_created,
    }


def record_chained_transaction_in_cursor(
    cur: sqlite3.Cursor,
    tx_data: Dict[str, Any],
    journal_id: Optional[str] = None,
) -> Dict[str, Any]:
    cur.execute("SELECT tx_hash FROM transactions ORDER BY timestamp DESC, rowid DESC LIMIT 1")
    last_row = cur.fetchone()
    prev_hash = last_row["tx_hash"] if last_row else "0" * 64

    amount_val = tx_data.get("amount", 0.0)
    amount_minor = tx_data.get("amount_minor")
    if amount_minor is None:
        amount_minor = to_minor_units(amount_val)

    tx_hash = compute_tx_chain_hash(prev_hash, tx_data)
    tx_record = {
        **tx_data,
        "amount": from_minor_units(amount_minor),
        "amount_minor": amount_minor,
        "journal_id": journal_id,
        "prev_tx_hash": prev_hash[:16],
        "tx_hash": tx_hash[:16],
    }

    cur.execute(
        """
        INSERT INTO transactions (
            tx_id, user_id, type, amount, amount_minor, currency, from_account, to_account,
            mandate_id, order_id, journal_id, status, prev_tx_hash, tx_hash, metadata_json, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            tx_record["tx_id"],
            tx_record.get("user_id", "USR_DEFAULT"),
            tx_record["type"],
            tx_record["amount"],
            amount_minor,
            tx_record.get("currency", "IDR"),
            tx_record.get("from_account"),
            tx_record.get("to_account") or tx_record.get("to_merchant"),
            tx_record.get("mandate_id") or tx_record.get("intent_mandate_id"),
            tx_record.get("order_id"),
            journal_id,
            tx_record["status"],
            prev_hash,
            tx_hash,
            json.dumps(tx_data, default=str),
            tx_record["timestamp"],
        ),
    )
    return tx_record


def record_chained_transaction(tx_data: Dict[str, Any], db_path: Optional[str] = None) -> Dict[str, Any]:
    with atomic_db_transaction(db_path) as cur:
        return record_chained_transaction_in_cursor(cur, tx_data)


def record_audit_log(
    *,
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str],
    status: str,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    cur: Optional[sqlite3.Cursor] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Appends an immutable, hash-chained security/financial audit event to `audit_logs`.
    """
    def _write(c: sqlite3.Cursor) -> Dict[str, Any]:
        c.execute("SELECT audit_hash FROM audit_logs ORDER BY created_at DESC, rowid DESC LIMIT 1")
        row = c.fetchone()
        prev_hash = row["audit_hash"] if row else "0" * 64
        now = datetime.now(timezone.utc).isoformat()
        audit_id = f"AUD_{uuid.uuid4().hex[:12].upper()}"
        payload = {
            "audit_id": audit_id,
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "status": status,
            "details": details or {},
            "created_at": now,
        }
        audit_hash = compute_tx_chain_hash(prev_hash, payload)
        c.execute(
            """
            INSERT INTO audit_logs (
                audit_id, user_id, action, resource_type, resource_id,
                status, ip_address, details_json, prev_audit_hash, audit_hash, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                audit_id,
                user_id,
                action,
                resource_type,
                resource_id,
                status,
                ip_address,
                json.dumps(details or {}, default=str),
                prev_hash,
                audit_hash,
                now,
            ),
        )
        return {**payload, "prev_audit_hash": prev_hash[:16], "audit_hash": audit_hash[:16]}

    if cur is not None:
        return _write(cur)
    with atomic_db_transaction(db_path) as c:
        return _write(c)


def check_and_register_nonce(
    nonce_input: str,
    mandate_id: str,
    cur: Optional[sqlite3.Cursor] = None,
    db_path: Optional[str] = None,
) -> bool:
    """
    Returns True if nonce is fresh and registers it; returns False if replay detected.
    """
    nonce_hash = hashlib.sha256(nonce_input.encode("utf-8")).hexdigest()

    def _check(c: sqlite3.Cursor) -> bool:
        c.execute("SELECT nonce_hash FROM used_nonces WHERE nonce_hash = ?", (nonce_hash,))
        if c.fetchone() is not None:
            return False
        c.execute(
            "INSERT INTO used_nonces (nonce_hash, mandate_id, created_at) VALUES (?, ?, ?)",
            (nonce_hash, mandate_id, datetime.now(timezone.utc).isoformat()),
        )
        return True

    if cur is not None:
        return _check(cur)
    with atomic_db_transaction(db_path) as c:
        return _check(c)


def sync_accounts_to_db(accounts: Dict[str, Dict[str, Any]], db_path: Optional[str] = None) -> None:
    with atomic_db_transaction(db_path) as cur:
        now = datetime.now(timezone.utc).isoformat()
        for acc_id, acc in accounts.items():
            bal_minor = acc.get("balance_minor")
            if bal_minor is None:
                bal_minor = to_minor_units(acc["balance"])
            bal_major = from_minor_units(bal_minor)
            cur.execute(
                """
                INSERT OR REPLACE INTO accounts (
                    account_id, user_id, account_type, name, currency, balance, balance_minor, status, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    acc_id,
                    acc.get("user_id", "USR_DEFAULT"),
                    acc.get("account_type", "ASSET"),
                    acc["name"],
                    acc["currency"],
                    bal_major,
                    bal_minor,
                    acc["status"],
                    now,
                ),
            )
