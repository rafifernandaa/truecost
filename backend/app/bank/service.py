import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Callable, Dict, List, Optional, Tuple
from nacl.signing import SigningKey

from app.schemas.mandate import CartMandate, IntentMandate
from app.bank.verifier import verify_cart_against_intent
from app.bank.database import (
    atomic_db_transaction,
    check_and_register_nonce,
    from_minor_units,
    get_db_connection,
    init_bank_db,
    post_double_entry_journal,
    record_audit_log,
    record_chained_transaction_in_cursor,
    sync_accounts_to_db,
    to_minor_units,
)


USER_ACCOUNT_IDS = (
    "ACC_USER_CHECKING",
    "ACC_USER_SINKING_POT",
    "ACC_EMERGENCY_BUFFER",
)


class UnauthorizedResourceAccessError(PermissionError):
    """Raised when a user attempts to access or mutate another user's financial records."""


class IdempotencyConflictError(ValueError):
    """Raised when an Idempotency-Key is reused with a different request payload."""


class SandboxBank:
    """
    Core Financial & Banking Service with SQLite-persisted double-entry ledger,
    integer minor-unit accounting, 3 ring-fenced user accounts (Checking, Sinking Pot Escrow,
    60d Emergency Buffer), counterparty clearing accounts, single-use disposable virtual cards,
    SHA-256 hash-chained transactions & audit logs, idempotency keys, and Ed25519 mandate verification.
    """

    def __init__(self, persist_state: bool = False, db_path: Optional[str] = None):
        self.db_path = db_path
        self.persist_state = persist_state
        init_bank_db(self.db_path)

        default_accounts: Dict[str, Dict[str, Any]] = {
            "ACC_USER_CHECKING": {
                "account_id": "ACC_USER_CHECKING",
                "user_id": "USR_DEFAULT",
                "account_type": "ASSET",
                "name": "Primary Student Checking Account",
                "currency": "IDR",
                "balance": 25000000.0,
                "balance_minor": to_minor_units(25000000),
                "status": "ACTIVE",
            },
            "ACC_USER_SINKING_POT": {
                "account_id": "ACC_USER_SINKING_POT",
                "user_id": "USR_DEFAULT",
                "account_type": "ASSET",
                "name": "Laptop Purchase Sinking Fund Pot",
                "currency": "IDR",
                "balance": 0.0,
                "balance_minor": 0,
                "status": "ACTIVE",
            },
            "ACC_EMERGENCY_BUFFER": {
                "account_id": "ACC_EMERGENCY_BUFFER",
                "user_id": "USR_DEFAULT",
                "account_type": "ASSET",
                "name": "60-Day Protected Living Buffer",
                "currency": "IDR",
                "balance": 10000000.0,
                "balance_minor": to_minor_units(10000000),
                "status": "RINGFENCED_PROTECTED",
            },
        }

        self.accounts: Dict[str, Dict[str, Any]] = {}
        self.intent_mandates: Dict[str, IntentMandate] = {}
        self.disposable_cards: Dict[str, Dict[str, Any]] = {}
        self.transactions: List[Dict[str, Any]] = []
        self.executed_orders: List[Dict[str, Any]] = []

        if self.persist_state:
            self._reload_from_db(fallback_accounts=default_accounts)
        else:
            self.accounts = default_accounts
            sync_accounts_to_db(self.accounts, self.db_path)

    def _reload_from_db(self, fallback_accounts: Optional[Dict[str, Dict[str, Any]]] = None) -> None:
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT account_id, user_id, account_type, name, currency, balance, balance_minor, status "
                "FROM accounts WHERE account_id IN ('ACC_USER_CHECKING', 'ACC_USER_SINKING_POT', 'ACC_EMERGENCY_BUFFER')"
            )
            rows = cur.fetchall()
            if rows:
                for r in rows:
                    bal_minor = int(r["balance_minor"])
                    self.accounts[r["account_id"]] = {
                        "account_id": r["account_id"],
                        "user_id": r["user_id"],
                        "account_type": r["account_type"],
                        "name": r["name"],
                        "currency": r["currency"],
                        "balance": from_minor_units(bal_minor),
                        "balance_minor": bal_minor,
                        "status": r["status"],
                    }
            elif fallback_accounts:
                self.accounts = fallback_accounts
                sync_accounts_to_db(self.accounts, self.db_path)

            cur.execute("SELECT mandate_id, mandate_json FROM intent_mandates_store ORDER BY created_at ASC")
            for r in cur.fetchall():
                try:
                    data = json.loads(r["mandate_json"])
                    self.intent_mandates[r["mandate_id"]] = IntentMandate(**data)
                except Exception:
                    pass

            cur.execute("SELECT * FROM disposable_cards_store ORDER BY created_at ASC")
            self.disposable_cards = {}
            for r in cur.fetchall():
                self.disposable_cards[r["card_id"]] = {
                    "card_id": r["card_id"],
                    "user_id": r["user_id"],
                    "cart_id": r["cart_id"],
                    "masked_pan": r["masked_pan"],
                    "currency": r["currency"],
                    "spending_limit": from_minor_units(int(r["spending_limit_minor"])),
                    "spending_limit_minor": int(r["spending_limit_minor"]),
                    "merchant_id": r["merchant_id"],
                    "status": r["status"],
                    "created_at": r["created_at"],
                }

            cur.execute("SELECT * FROM executed_orders ORDER BY timestamp ASC")
            self.executed_orders = []
            for r in cur.fetchall():
                self.executed_orders.append(
                    {
                        "order_id": r["order_id"],
                        "user_id": r["user_id"],
                        "cart_id": r["cart_id"],
                        "intent_mandate_id": r["intent_mandate_id"],
                        "item_title": r["item_title"],
                        "merchant_name": r["merchant_name"],
                        "sticker_price": float(r["sticker_price"]),
                        "final_landed_cost": from_minor_units(int(r["final_landed_cost_minor"]))
                        if r["final_landed_cost_minor"]
                        else float(r["final_landed_cost"]),
                        "final_landed_cost_minor": int(r["final_landed_cost_minor"]),
                        "savings_amount": float(r["savings_amount"]),
                        "currency": r["currency"],
                        "payment_method": r["payment_method"],
                        "effective_apr": float(r["effective_apr"]),
                        "disposable_card_id": r["disposable_card_id"],
                        "debit_source": r["debit_source"],
                        "status": r["status"],
                        "timestamp": r["timestamp"],
                    }
                )

            cur.execute("SELECT * FROM transactions ORDER BY timestamp ASC, rowid ASC")
            self.transactions = []
            for r in cur.fetchall():
                meta = {}
                if r["metadata_json"]:
                    try:
                        meta = json.loads(r["metadata_json"])
                    except Exception:
                        meta = {}
                self.transactions.append(
                    {
                        **meta,
                        "tx_id": r["tx_id"],
                        "user_id": r["user_id"],
                        "type": r["type"],
                        "amount": from_minor_units(int(r["amount_minor"]))
                        if r["amount_minor"]
                        else float(r["amount"]),
                        "amount_minor": int(r["amount_minor"]),
                        "currency": r["currency"],
                        "from_account": r["from_account"],
                        "to_account": r["to_account"],
                        "mandate_id": r["mandate_id"],
                        "order_id": r["order_id"],
                        "journal_id": r["journal_id"],
                        "status": r["status"],
                        "prev_tx_hash": str(r["prev_tx_hash"])[:16],
                        "tx_hash": str(r["tx_hash"])[:16],
                        "timestamp": r["timestamp"],
                    }
                )
        finally:
            conn.close()

    def _refresh_in_memory_accounts_from_cursor(self, cur) -> None:
        cur.execute(
            "SELECT account_id, user_id, account_type, name, currency, balance, balance_minor, status "
            "FROM accounts WHERE account_id IN ('ACC_USER_CHECKING', 'ACC_USER_SINKING_POT', 'ACC_EMERGENCY_BUFFER')"
        )
        for r in cur.fetchall():
            bal_minor = int(r["balance_minor"])
            self.accounts[r["account_id"]] = {
                "account_id": r["account_id"],
                "user_id": r["user_id"],
                "account_type": r["account_type"],
                "name": r["name"],
                "currency": r["currency"],
                "balance": from_minor_units(bal_minor),
                "balance_minor": bal_minor,
                "status": r["status"],
            }

    def verify_user_authorization(self, requesting_user_id: str, owner_user_id: str = "USR_DEFAULT") -> None:
        """
        Enforces resource-level authorization so a user cannot access or mutate another user's records.
        """
        if requesting_user_id != owner_user_id:
            record_audit_log(
                user_id=requesting_user_id,
                action="UNAUTHORIZED_RESOURCE_ACCESS_BLOCKED",
                resource_type="USER_ACCOUNT",
                resource_id=owner_user_id,
                status="DENIED",
                details={"requesting_user_id": requesting_user_id, "owner_user_id": owner_user_id},
                db_path=self.db_path,
            )
            raise UnauthorizedResourceAccessError(
                f"User '{requesting_user_id}' is not authorized to access resources owned by '{owner_user_id}'."
            )

    def execute_idempotent(
        self,
        *,
        idempotency_key: Optional[str],
        user_id: str,
        endpoint: str,
        request_payload: Dict[str, Any],
        operation_fn: Callable[[], Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Executes `operation_fn` with strict idempotency protection.
        If `idempotency_key` has already been processed for `(user_id, endpoint)`:
        - If the payload hash matches, returns the cached response without re-running the financial operation.
        - If the payload hash differs, raises `IdempotencyConflictError`.
        """
        if not idempotency_key:
            return operation_fn()

        canonical_req = json.dumps(request_payload, sort_keys=True, default=str)
        req_hash = hashlib.sha256(canonical_req.encode("utf-8")).hexdigest()

        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT request_hash, response_json FROM idempotency_keys
                WHERE idempotency_key = ? AND user_id = ? AND endpoint = ?
                """,
                (idempotency_key, user_id, endpoint),
            )
            existing = cur.fetchone()
            if existing:
                if existing["request_hash"] != req_hash:
                    raise IdempotencyConflictError(
                        f"IDEMPOTENCY_KEY_CONFLICT: Key '{idempotency_key}' was already used with different parameters."
                    )
                cached = json.loads(existing["response_json"])
                cached["idempotent_replay"] = True
                return cached
        finally:
            conn.close()

        result = operation_fn()

        now = datetime.now(timezone.utc)
        expires = (now + timedelta(hours=24)).isoformat()
        with atomic_db_transaction(self.db_path) as cur2:
            cur2.execute(
                """
                INSERT OR IGNORE INTO idempotency_keys (
                    idempotency_key, user_id, endpoint, request_hash,
                    response_status, response_json, created_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    idempotency_key,
                    user_id,
                    endpoint,
                    req_hash,
                    200,
                    json.dumps(result, default=str),
                    now.isoformat(),
                    expires,
                ),
            )
        result["idempotent_replay"] = False
        return result

    def get_account_summary(self, user_id: str = "USR_DEFAULT") -> Dict[str, Any]:
        self.verify_user_authorization(user_id, "USR_DEFAULT")
        if self.persist_state:
            self._reload_from_db()

        checking_minor = int(self.accounts["ACC_USER_CHECKING"].get("balance_minor", to_minor_units(self.accounts["ACC_USER_CHECKING"]["balance"])))
        pot_minor = int(self.accounts["ACC_USER_SINKING_POT"].get("balance_minor", to_minor_units(self.accounts["ACC_USER_SINKING_POT"]["balance"])))
        buffer_minor = int(self.accounts.get("ACC_EMERGENCY_BUFFER", {}).get("balance_minor", to_minor_units(10000000)))

        checking = from_minor_units(checking_minor)
        pot = from_minor_units(pot_minor)
        buffer_acc = from_minor_units(buffer_minor)
        fx_aud = Decimal("10400")

        return {
            "user_id": user_id,
            "accounts": list(self.accounts.values()),
            "checking_balance_idr": checking,
            "checking_balance_minor": checking_minor,
            "checking_balance_aud": float((Decimal(str(checking)) / fx_aud).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            "sinking_pot_idr": pot,
            "sinking_pot_minor": pot_minor,
            "sinking_pot_aud": float((Decimal(str(pot)) / fx_aud).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            "emergency_buffer_idr": buffer_acc,
            "emergency_buffer_minor": buffer_minor,
            "emergency_buffer_aud": float((Decimal(str(buffer_acc)) / fx_aud).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            "total_liquid_idr": from_minor_units(checking_minor + pot_minor),
            "total_liquid_minor": checking_minor + pot_minor,
            "active_intent_mandates": len(self.intent_mandates),
            "executed_orders_count": len(self.executed_orders),
            "disposable_cards_count": len(self.disposable_cards),
        }

    def get_ledger_summary(self, user_id: str = "USR_DEFAULT", limit: int = 50) -> Dict[str, Any]:
        """
        Returns the double-entry accounting journals, postings, and mathematical balance proof.
        """
        self.verify_user_authorization(user_id, "USR_DEFAULT")
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT
                    COALESCE(SUM(CASE WHEN direction = 'DEBIT' THEN amount_minor ELSE 0 END), 0) AS sum_debit,
                    COALESCE(SUM(CASE WHEN direction = 'CREDIT' THEN amount_minor ELSE 0 END), 0) AS sum_credit,
                    COUNT(*) AS entry_count
                FROM ledger_entries
                """
            )
            agg = cur.fetchone()
            sum_debit = int(agg["sum_debit"]) if agg else 0
            sum_credit = int(agg["sum_credit"]) if agg else 0
            entry_count = int(agg["entry_count"]) if agg else 0

            cur.execute("SELECT * FROM ledger_journals ORDER BY created_at DESC, rowid DESC LIMIT ?", (limit,))
            journals = [dict(r) for r in cur.fetchall()]

            cur.execute("SELECT * FROM ledger_entries ORDER BY created_at DESC, rowid DESC LIMIT ?", (limit * 2,))
            entries = [dict(r) for r in cur.fetchall()]

            return {
                "is_balanced": sum_debit == sum_credit,
                "total_debit_minor": sum_debit,
                "total_credit_minor": sum_credit,
                "total_debit_major": from_minor_units(sum_debit),
                "total_credit_major": from_minor_units(sum_credit),
                "total_entries": entry_count,
                "journals": journals,
                "entries": entries,
            }
        finally:
            conn.close()

    def reverse_journal(
        self,
        journal_id: str,
        reason: str = "Administrative or Refund Reversal",
        user_id: str = "USR_DEFAULT",
    ) -> Dict[str, Any]:
        """
        Creates an immutable reversing double-entry journal for `journal_id`.
        Posted ledger entries are never updated or deleted; instead, inverse DEBIT/CREDIT postings
        are recorded in a new reversing journal.
        """
        self.verify_user_authorization(user_id, "USR_DEFAULT")
        with atomic_db_transaction(self.db_path) as cur:
            cur.execute("SELECT * FROM ledger_journals WHERE journal_id = ?", (journal_id,))
            orig_journal = cur.fetchone()
            if not orig_journal:
                raise ValueError(f"Journal '{journal_id}' not found.")

            cur.execute("SELECT journal_id FROM ledger_journals WHERE reverses_journal_id = ?", (journal_id,))
            if cur.fetchone():
                raise ValueError(f"Journal '{journal_id}' has already been reversed.")

            cur.execute("SELECT * FROM ledger_entries WHERE journal_id = ? ORDER BY rowid ASC", (journal_id,))
            orig_entries = cur.fetchall()
            if not orig_entries:
                raise ValueError(f"Journal '{journal_id}' has no ledger entries.")

            reverse_postings: List[Tuple[str, str, int]] = []
            for entry in orig_entries:
                inv_dir = "CREDIT" if entry["direction"] == "DEBIT" else "DEBIT"
                reverse_postings.append((entry["account_id"], inv_dir, int(entry["amount_minor"])))

            rev_tx_id = str(uuid.uuid4())
            rev_journal = post_double_entry_journal(
                cur,
                tx_id=rev_tx_id,
                user_id=user_id,
                entry_type=f"REVERSAL_{orig_journal['entry_type']}",
                description=f"Reversal of {journal_id}: {reason}",
                currency=orig_journal["currency"],
                postings=reverse_postings,
                is_reversal=True,
                reverses_journal_id=journal_id,
            )

            tx_rec = record_chained_transaction_in_cursor(
                cur,
                {
                    "tx_id": rev_tx_id,
                    "user_id": user_id,
                    "type": "JOURNAL_REVERSAL",
                    "amount": from_minor_units(int(orig_journal["total_debit_minor"])),
                    "amount_minor": int(orig_journal["total_debit_minor"]),
                    "currency": orig_journal["currency"],
                    "from_account": "DOUBLE_ENTRY_REVERSAL",
                    "to_account": journal_id,
                    "reason": reason,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "status": "REVERSED",
                },
                journal_id=rev_journal["journal_id"],
            )
            record_audit_log(
                user_id=user_id,
                action="LEDGER_JOURNAL_REVERSED",
                resource_type="LEDGER_JOURNAL",
                resource_id=journal_id,
                status="SUCCESS",
                details={"reversal_journal_id": rev_journal["journal_id"], "reason": reason},
                cur=cur,
            )
            self._refresh_in_memory_accounts_from_cursor(cur)
            self.transactions.append(tx_rec)
            return {
                "status": "REVERSED",
                "original_journal_id": journal_id,
                "reversal_journal": rev_journal,
                "transaction": tx_rec,
            }

    def deposit_income(
        self,
        amount_idr: float,
        source: str = "Monthly Salary & Allowance",
        user_id: str = "USR_DEFAULT",
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Stage 1 of Real Money Flow: Credits user income, automatically routing 20% to the
        60-Day Protected Emergency Buffer and 80% to Primary Checking Safe-to-Spend
        via an atomic, balanced double-entry journal.
        """
        self.verify_user_authorization(user_id, "USR_DEFAULT")

        def _op() -> Dict[str, Any]:
            if amount_idr <= 0 or amount_idr > 500_000_000:
                raise ValueError("Deposit amount must be between 1 and 500,000,000 IDR.")

            total_minor = to_minor_units(amount_idr)
            buffer_minor = int(
                (Decimal(total_minor) * Decimal("0.20")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            )
            checking_minor = total_minor - buffer_minor

            # Ensure our SQLite table has the exact current in-memory state prior to atomic journal posting
            sync_accounts_to_db(self.accounts, self.db_path)

            with atomic_db_transaction(self.db_path) as cur:
                tx_id = str(uuid.uuid4())
                journal = post_double_entry_journal(
                    cur,
                    tx_id=tx_id,
                    user_id=user_id,
                    entry_type="INCOME_SPLIT_DEPOSIT",
                    description=f"Income deposit from {source} (80% Checking / 20% Protected Buffer)",
                    currency="IDR",
                    postings=[
                        ("ACC_EXTERNAL_INCOME_SOURCE", "DEBIT", total_minor),
                        ("ACC_USER_CHECKING", "CREDIT", checking_minor),
                        ("ACC_EMERGENCY_BUFFER", "CREDIT", buffer_minor),
                    ],
                )
                tx = record_chained_transaction_in_cursor(
                    cur,
                    {
                        "tx_id": tx_id,
                        "user_id": user_id,
                        "type": "INCOME_SPLIT_DEPOSIT",
                        "amount": from_minor_units(total_minor),
                        "amount_minor": total_minor,
                        "checking_credited": from_minor_units(checking_minor),
                        "buffer_credited": from_minor_units(buffer_minor),
                        "currency": "IDR",
                        "from_account": source,
                        "to_account": "ACC_USER_CHECKING+ACC_EMERGENCY_BUFFER",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "status": "COMPLETED",
                    },
                    journal_id=journal["journal_id"],
                )
                record_audit_log(
                    user_id=user_id,
                    action="INCOME_DEPOSIT_POSTED",
                    resource_type="ACCOUNT",
                    resource_id="ACC_USER_CHECKING",
                    status="SUCCESS",
                    details={
                        "amount_minor": total_minor,
                        "checking_minor": checking_minor,
                        "buffer_minor": buffer_minor,
                        "journal_id": journal["journal_id"],
                    },
                    cur=cur,
                )
                self._refresh_in_memory_accounts_from_cursor(cur)

            self.transactions.append(tx)
            return {
                "status": "DEPOSITED",
                "amount_idr": from_minor_units(total_minor),
                "amount_minor": total_minor,
                "checking_credited_idr": from_minor_units(checking_minor),
                "buffer_credited_idr": from_minor_units(buffer_minor),
                "checking_balance_idr": self.accounts["ACC_USER_CHECKING"]["balance"],
                "emergency_buffer_idr": self.accounts["ACC_EMERGENCY_BUFFER"]["balance"],
                "journal_id": journal["journal_id"],
                "transaction": tx,
            }

        return self.execute_idempotent(
            idempotency_key=idempotency_key,
            user_id=user_id,
            endpoint="POST:/api/bank/deposit",
            request_payload={"amount_idr": amount_idr, "source": source},
            operation_fn=_op,
        )

    def register_intent_mandate(
        self,
        mandate: IntentMandate,
        user_id: str = "USR_DEFAULT",
    ) -> Dict[str, Any]:
        """
        Stage 2 of Real Money Flow: Verifies Ed25519 signature + anti-replay nonce,
        and locks budget into the Sinking Pot Escrow via an atomic double-entry journal.
        """
        self.verify_user_authorization(user_id, "USR_DEFAULT")
        if not mandate.verify_signature():
            raise ValueError("Cannot register mandate: Invalid cryptographic signature.")

        sync_accounts_to_db(self.accounts, self.db_path)

        with atomic_db_transaction(self.db_path) as cur:
            nonce_key = f"{mandate.mandate_id}:{mandate.user_signature}"
            if not check_and_register_nonce(nonce_key, mandate.mandate_id, cur=cur):
                raise ValueError("REPLAY_ATTACK_DETECTED: Mandate signature has already been registered.")

            cur.execute("SELECT balance_minor FROM accounts WHERE account_id = 'ACC_USER_CHECKING'")
            checking_minor = int(cur.fetchone()["balance_minor"])
            budget_minor = to_minor_units(mandate.max_budget)
            reserve_minor = min(checking_minor, budget_minor)

            tx_id = str(uuid.uuid4())
            journal_id: Optional[str] = None
            if reserve_minor > 0:
                journal = post_double_entry_journal(
                    cur,
                    tx_id=tx_id,
                    user_id=user_id,
                    entry_type="RESERVE_SINKING_POT",
                    description=f"Escrow reservation for IntentMandate {mandate.mandate_id}",
                    currency=mandate.currency,
                    postings=[
                        ("ACC_USER_CHECKING", "DEBIT", reserve_minor),
                        ("ACC_USER_SINKING_POT", "CREDIT", reserve_minor),
                    ],
                )
                journal_id = journal["journal_id"]

            cur.execute(
                """
                INSERT OR REPLACE INTO intent_mandates_store (
                    mandate_id, user_id, user_public_key, item_query, max_budget_minor,
                    currency, mandate_json, status, created_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?)
                """,
                (
                    mandate.mandate_id,
                    user_id,
                    mandate.user_public_key,
                    mandate.item_query,
                    budget_minor,
                    mandate.currency,
                    mandate.model_dump_json(),
                    mandate.created_at,
                    mandate.expires_at,
                ),
            )

            tx = record_chained_transaction_in_cursor(
                cur,
                {
                    "tx_id": tx_id,
                    "user_id": user_id,
                    "type": "RESERVE_SINKING_POT",
                    "amount": from_minor_units(reserve_minor),
                    "amount_minor": reserve_minor,
                    "currency": mandate.currency,
                    "from_account": "ACC_USER_CHECKING",
                    "to_account": "ACC_USER_SINKING_POT",
                    "mandate_id": mandate.mandate_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "status": "COMPLETED",
                },
                journal_id=journal_id,
            )
            record_audit_log(
                user_id=user_id,
                action="INTENT_MANDATE_REGISTERED",
                resource_type="INTENT_MANDATE",
                resource_id=mandate.mandate_id,
                status="SUCCESS",
                details={"reserved_minor": reserve_minor, "journal_id": journal_id},
                cur=cur,
            )
            self._refresh_in_memory_accounts_from_cursor(cur)

        self.intent_mandates[mandate.mandate_id] = mandate
        self.transactions.append(tx)

        return {
            "status": "REGISTERED",
            "mandate_id": mandate.mandate_id,
            "reserved_funds": from_minor_units(reserve_minor),
            "reserved_funds_minor": reserve_minor,
            "pot_balance": self.accounts["ACC_USER_SINKING_POT"]["balance"],
            "checking_balance": self.accounts["ACC_USER_CHECKING"]["balance"],
            "journal_id": journal_id,
            "tx_hash": tx.get("tx_hash"),
        }

    def generate_disposable_card(self, cart: CartMandate, user_id: str = "USR_DEFAULT") -> Dict[str, Any]:
        """
        Generates a Revolut-style single-use virtual card token locked to the exact cart amount and merchant.
        """
        card_id = f"VCARD_{uuid.uuid4().hex[:12].upper()}"
        limit_minor = to_minor_units(cart.landed_cost)
        card = {
            "card_id": card_id,
            "user_id": user_id,
            "cart_id": cart.cart_id,
            "masked_pan": f"4532-XXXX-XXXX-{uuid.uuid4().hex[:4].upper()}",
            "currency": cart.currency,
            "spending_limit": from_minor_units(limit_minor),
            "spending_limit_minor": limit_minor,
            "merchant_id": cart.merchant_id,
            "status": "ACTIVE_SINGLE_USE",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.disposable_cards[card_id] = card
        return card

    def execute_cart_mandate(
        self,
        cart: CartMandate,
        user_override_token: Optional[str] = None,
        user_id: str = "USR_DEFAULT",
    ) -> Dict[str, Any]:
        """
        Stage 3 of Real Money Flow: Performs independent bank-side Ed25519 + policy verification,
        issues a single-use virtual card, and settles via an atomic double-entry journal.
        """
        self.verify_user_authorization(user_id, "USR_DEFAULT")
        intent = self.intent_mandates.get(cart.intent_mandate_id)
        if not intent:
            return {
                "success": False,
                "error_code": "MANDATE_NOT_FOUND",
                "message": f"Parent Intent Mandate {cart.intent_mandate_id} is not registered.",
            }

        # 1. Independent policy verification
        valid, reason = verify_cart_against_intent(intent, cart, user_override_token)
        if not valid:
            with atomic_db_transaction(self.db_path) as cur:
                rejection_log = record_chained_transaction_in_cursor(
                    cur,
                    {
                        "tx_id": str(uuid.uuid4()),
                        "user_id": user_id,
                        "type": "PURCHASE_REJECTED",
                        "amount": cart.landed_cost,
                        "amount_minor": to_minor_units(cart.landed_cost),
                        "currency": cart.currency,
                        "cart_id": cart.cart_id,
                        "intent_mandate_id": intent.mandate_id,
                        "reason": reason,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "status": "REJECTED_BY_BANK_POLICY",
                    },
                )
                record_audit_log(
                    user_id=user_id,
                    action="CART_MANDATE_REJECTED",
                    resource_type="CART_MANDATE",
                    resource_id=cart.cart_id,
                    status="REJECTED",
                    details={"reason": reason, "intent_mandate_id": intent.mandate_id},
                    cur=cur,
                )
            self.transactions.append(rejection_log)
            return {
                "success": False,
                "error_code": "BANK_POLICY_VIOLATION",
                "message": reason,
                "rejection_log": rejection_log,
            }

        sync_accounts_to_db(self.accounts, self.db_path)
        debit_minor = to_minor_units(cart.landed_cost)

        with atomic_db_transaction(self.db_path) as cur:
            cur.execute("SELECT balance_minor FROM accounts WHERE account_id = 'ACC_USER_SINKING_POT'")
            pot_minor = int(cur.fetchone()["balance_minor"])
            cur.execute("SELECT balance_minor FROM accounts WHERE account_id = 'ACC_USER_CHECKING'")
            checking_minor = int(cur.fetchone()["balance_minor"])

            postings: List[Tuple[str, str, int]] = []
            if pot_minor >= debit_minor:
                postings.append(("ACC_USER_SINKING_POT", "DEBIT", debit_minor))
                postings.append(("ACC_MERCHANT_SETTLEMENT_CLEARING", "CREDIT", debit_minor))
                debit_from = "ACC_USER_SINKING_POT"
            elif (pot_minor + checking_minor) >= debit_minor:
                from_pot_minor = pot_minor
                from_checking_minor = debit_minor - from_pot_minor
                if from_pot_minor > 0:
                    postings.append(("ACC_USER_SINKING_POT", "DEBIT", from_pot_minor))
                if from_checking_minor > 0:
                    postings.append(("ACC_USER_CHECKING", "DEBIT", from_checking_minor))
                postings.append(("ACC_MERCHANT_SETTLEMENT_CLEARING", "CREDIT", debit_minor))
                debit_from = "COMBINED_POT_AND_CHECKING"
            else:
                return {
                    "success": False,
                    "error_code": "INSUFFICIENT_FUNDS",
                    "message": f"Insufficient balance to debit {from_minor_units(debit_minor):,.2f} {cart.currency}.",
                }

            tx_id = str(uuid.uuid4())
            journal = post_double_entry_journal(
                cur,
                tx_id=tx_id,
                user_id=user_id,
                entry_type="PURCHASE_SETTLEMENT",
                description=f"CartMandate settlement {cart.cart_id} to {cart.merchant_name}",
                currency=cart.currency,
                postings=postings,
            )

            disposable_card = self.generate_disposable_card(cart, user_id=user_id)
            disposable_card["status"] = "CONSUMED_DESTROYED"

            cur.execute(
                """
                INSERT OR REPLACE INTO disposable_cards_store (
                    card_id, user_id, cart_id, masked_pan, currency,
                    spending_limit_minor, merchant_id, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    disposable_card["card_id"],
                    user_id,
                    disposable_card["cart_id"],
                    disposable_card["masked_pan"],
                    disposable_card["currency"],
                    disposable_card["spending_limit_minor"],
                    disposable_card["merchant_id"],
                    disposable_card["status"],
                    disposable_card["created_at"],
                ),
            )

            now_iso = datetime.now(timezone.utc).isoformat()
            savings_val = max(0.0, float(intent.max_budget) - from_minor_units(debit_minor))
            order_record = {
                "order_id": f"ORD_{uuid.uuid4().hex[:8].upper()}",
                "user_id": user_id,
                "cart_id": cart.cart_id,
                "intent_mandate_id": intent.mandate_id,
                "item_title": cart.item_title,
                "merchant_name": cart.merchant_name,
                "sticker_price": cart.sticker_price,
                "final_landed_cost": from_minor_units(debit_minor),
                "final_landed_cost_minor": debit_minor,
                "savings_amount": round(savings_val, 2),
                "currency": cart.currency,
                "payment_method": cart.payment_method,
                "effective_apr": cart.effective_apr,
                "disposable_card_id": disposable_card["card_id"],
                "debit_source": debit_from,
                "timestamp": now_iso,
                "status": "SETTLED_CONFIRMED",
            }

            cur.execute(
                """
                INSERT INTO executed_orders (
                    order_id, user_id, cart_id, intent_mandate_id, item_title, merchant_name,
                    sticker_price, final_landed_cost, final_landed_cost_minor, savings_amount,
                    currency, payment_method, effective_apr, disposable_card_id,
                    debit_source, status, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order_record["order_id"],
                    user_id,
                    order_record["cart_id"],
                    order_record["intent_mandate_id"],
                    order_record["item_title"],
                    order_record["merchant_name"],
                    order_record["sticker_price"],
                    order_record["final_landed_cost"],
                    order_record["final_landed_cost_minor"],
                    order_record["savings_amount"],
                    order_record["currency"],
                    order_record["payment_method"],
                    order_record["effective_apr"],
                    order_record["disposable_card_id"],
                    order_record["debit_source"],
                    order_record["status"],
                    order_record["timestamp"],
                ),
            )

            tx_log = record_chained_transaction_in_cursor(
                cur,
                {
                    "tx_id": tx_id,
                    "user_id": user_id,
                    "type": "PURCHASE_SETTLEMENT",
                    "order_id": order_record["order_id"],
                    "amount": from_minor_units(debit_minor),
                    "amount_minor": debit_minor,
                    "currency": cart.currency,
                    "from_account": debit_from,
                    "to_merchant": cart.merchant_name,
                    "timestamp": order_record["timestamp"],
                    "status": "COMPLETED",
                },
                journal_id=journal["journal_id"],
            )
            record_audit_log(
                user_id=user_id,
                action="CART_MANDATE_SETTLED",
                resource_type="ORDER",
                resource_id=order_record["order_id"],
                status="SUCCESS",
                details={
                    "cart_id": cart.cart_id,
                    "debit_minor": debit_minor,
                    "journal_id": journal["journal_id"],
                    "disposable_card_id": disposable_card["card_id"],
                },
                cur=cur,
            )
            self._refresh_in_memory_accounts_from_cursor(cur)

        self.executed_orders.append(order_record)
        self.transactions.append(tx_log)

        return {
            "success": True,
            "order": order_record,
            "transaction": tx_log,
            "journal_id": journal["journal_id"],
            "remaining_checking_balance": self.accounts["ACC_USER_CHECKING"]["balance"],
            "remaining_pot_balance": self.accounts["ACC_USER_SINKING_POT"]["balance"],
            "emergency_buffer_balance": self.accounts["ACC_EMERGENCY_BUFFER"]["balance"],
            "disposable_card": disposable_card,
        }

    def execute_real_case_flow(
        self,
        item_title: str,
        max_budget_idr: float,
        optimal_landed_idr: float,
        merchant_id: str = "MERCHANT_LENOVO_AU",
        merchant_name: str = "Lenovo Official Australia",
        is_scam: bool = False,
        scam_z_score: float = -0.45,
        mode: str = "reserve_and_settle",
        user_id: str = "USR_DEFAULT",
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        End-to-end cryptographic money flow for real user interaction with double-entry ledger postings.
        """
        self.verify_user_authorization(user_id, "USR_DEFAULT")

        def _op() -> Dict[str, Any]:
            user_key = SigningKey.generate()
            agent_key = SigningKey.generate()
            user_pub = user_key.verify_key.encode().hex()
            agent_pub = agent_key.verify_key.encode().hex()

            now = datetime.now(timezone.utc)
            mandate_id = f"MND_{uuid.uuid4().hex[:8].upper()}"
            expires_at = (now + timedelta(days=14)).isoformat()

            sync_accounts_to_db(self.accounts, self.db_path)

            # Consolidate prior unspent Sinking Pot funds back into Checking via balanced journal
            with atomic_db_transaction(self.db_path) as cur:
                cur.execute("SELECT balance_minor FROM accounts WHERE account_id = 'ACC_USER_SINKING_POT'")
                existing_pot_minor = int(cur.fetchone()["balance_minor"])
                if existing_pot_minor > 0:
                    cons_tx_id = str(uuid.uuid4())
                    post_double_entry_journal(
                        cur,
                        tx_id=cons_tx_id,
                        user_id=user_id,
                        entry_type="ESCROW_CONSOLIDATION",
                        description="Consolidate prior Sinking Pot balance back to Checking",
                        currency="IDR",
                        postings=[
                            ("ACC_USER_SINKING_POT", "DEBIT", existing_pot_minor),
                            ("ACC_USER_CHECKING", "CREDIT", existing_pot_minor),
                        ],
                    )
                    self._refresh_in_memory_accounts_from_cursor(cur)

            intent = IntentMandate(
                mandate_id=mandate_id,
                user_public_key=user_pub,
                item_query=item_title,
                max_budget=max_budget_idr,
                currency="IDR",
                allowed_payment_methods=["CASH", "DEBIT", "BNPL_VERIFIED"],
                max_acceptable_apr=0.10,
                allow_cross_border=True,
                cooling_off_seconds=0,
                created_at=now.isoformat(),
                expires_at=expires_at,
            )
            sig_hex = user_key.sign(intent.canonical_bytes()).signature.hex()
            intent.user_signature = sig_hex

            reg_res = self.register_intent_mandate(intent, user_id=user_id)

            if mode == "reserve_only":
                return {
                    "success": True,
                    "stage": "ESCROW_RESERVED_WAITING_VALLEY",
                    "mandate_id": mandate_id,
                    "ed25519_public_key": user_pub[:16] + "...",
                    "ed25519_signature": sig_hex[:24] + "...",
                    "reserved_idr": reg_res["reserved_funds"],
                    "checking_balance_idr": self.accounts["ACC_USER_CHECKING"]["balance"],
                    "sinking_pot_idr": self.accounts["ACC_USER_SINKING_POT"]["balance"],
                    "emergency_buffer_idr": self.accounts["ACC_EMERGENCY_BUFFER"]["balance"],
                }

            cart = CartMandate(
                cart_id=f"CART_{uuid.uuid4().hex[:8].upper()}",
                intent_mandate_id=mandate_id,
                merchant_id=merchant_id,
                merchant_name=merchant_name,
                item_title=item_title,
                sticker_price=max_budget_idr,
                currency="IDR",
                landed_cost=optimal_landed_idr,
                payment_method="DEBIT",
                effective_apr=0.0,
                scam_score=0.92 if is_scam else 0.05,
                created_at=now.isoformat(),
                agent_public_key=agent_pub,
            )
            cart.agent_signature = agent_key.sign(cart.canonical_bytes()).signature.hex()

            exec_res = self.execute_cart_mandate(cart, user_id=user_id)

            savings_refunded = 0.0
            if exec_res.get("success"):
                with atomic_db_transaction(self.db_path) as cur:
                    cur.execute("SELECT balance_minor FROM accounts WHERE account_id = 'ACC_USER_SINKING_POT'")
                    rem_pot_minor = int(cur.fetchone()["balance_minor"])
                    if rem_pot_minor > 0:
                        savings_refunded = from_minor_units(rem_pot_minor)
                        ref_tx_id = str(uuid.uuid4())
                        ref_journal = post_double_entry_journal(
                            cur,
                            tx_id=ref_tx_id,
                            user_id=user_id,
                            entry_type="SAVINGS_ESCROW_REFUND",
                            description=f"Refund unspent escrow savings for {mandate_id} back to Checking",
                            currency="IDR",
                            postings=[
                                ("ACC_USER_SINKING_POT", "DEBIT", rem_pot_minor),
                                ("ACC_USER_CHECKING", "CREDIT", rem_pot_minor),
                            ],
                        )
                        refund_tx = record_chained_transaction_in_cursor(
                            cur,
                            {
                                "tx_id": ref_tx_id,
                                "user_id": user_id,
                                "type": "SAVINGS_ESCROW_REFUND",
                                "amount": savings_refunded,
                                "amount_minor": rem_pot_minor,
                                "currency": "IDR",
                                "from_account": "ACC_USER_SINKING_POT",
                                "to_account": "ACC_USER_CHECKING",
                                "mandate_id": mandate_id,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "status": "COMPLETED",
                            },
                            journal_id=ref_journal["journal_id"],
                        )
                        self._refresh_in_memory_accounts_from_cursor(cur)
                        self.transactions.append(refund_tx)

            return {
                **exec_res,
                "mandate_id": mandate_id,
                "ed25519_public_key": user_pub[:16] + "...",
                "ed25519_signature": sig_hex[:24] + "...",
                "savings_refunded": savings_refunded,
                "checking_balance_idr": self.accounts["ACC_USER_CHECKING"]["balance"],
                "sinking_pot_idr": self.accounts["ACC_USER_SINKING_POT"]["balance"],
                "emergency_buffer_idr": self.accounts["ACC_EMERGENCY_BUFFER"]["balance"],
            }

        return self.execute_idempotent(
            idempotency_key=idempotency_key,
            user_id=user_id,
            endpoint="POST:/api/bank/real-flow",
            request_payload={
                "item_title": item_title,
                "max_budget_idr": max_budget_idr,
                "optimal_landed_idr": optimal_landed_idr,
                "merchant_id": merchant_id,
                "mode": mode,
                "is_scam": is_scam,
            },
            operation_fn=_op,
        )


# Singleton instance for the application runtime (loads persisted state from SQLite)
bank_service = SandboxBank(persist_state=True)
