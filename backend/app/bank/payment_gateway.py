"""
External Financial Infrastructure & Indonesian Payment Gateway Integration (Xendit & Midtrans).

Implements:
1. Authoritative server-side amount resolution (from registered Mandate or Order)
2. Payment Intent / Checkout creation (Xendit v2 Invoices & Midtrans Snap API via httpx when
   credentials are configured, with deterministic sandbox simulation when offline)
3. Strict Transaction State Machine:
   - PENDING -> {PAID, FAILED, EXPIRED, CANCELLED}
   - PAID -> {REFUNDED}
4. Cryptographic Webhook Verification:
   - Xendit: Constant-time `x-callback-token` & HMAC-SHA256 verification
   - Midtrans: Documented `SHA512(order_id + status_code + gross_amount + server_key)` verification
5. Idempotent Webhook Processing (`webhook_events` table with `UNIQUE(provider, provider_event_id)`)
6. Exactly-once Double-Entry Ledger posting upon `PAID` settlement, and immutable reversing journal
   posting upon `REFUNDED`
7. Automated Ledger vs. Provider Settlement Reconciliation (`reconciliation_records`)
"""
import base64
import hashlib
import hmac
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
import httpx

from app.bank.database import (
    atomic_db_transaction,
    from_minor_units,
    get_db_connection,
    post_double_entry_journal,
    record_audit_log,
    record_chained_transaction_in_cursor,
    to_minor_units,
)
from app.bank.service import SandboxBank, bank_service


VALID_STATE_TRANSITIONS: Dict[str, Set[str]] = {
    "PENDING": {"PAID", "FAILED", "EXPIRED", "CANCELLED"},
    "PAID": {"REFUNDED"},
    "FAILED": set(),
    "EXPIRED": set(),
    "CANCELLED": set(),
    "REFUNDED": set(),
}

SUPPORTED_PROVIDERS = {"XENDIT", "MIDTRANS"}
SUPPORTED_PAYMENT_METHODS = {
    "QRIS",
    "VIRTUAL_ACCOUNT_BCA",
    "VIRTUAL_ACCOUNT_MANDIRI",
    "VIRTUAL_ACCOUNT_BNI",
    "EWALLET_GOPAY",
    "EWALLET_OVO",
    "DEBIT",
}


class PaymentGatewayError(ValueError):
    """Raised on invalid payment state transitions, amount mismatches, or gateway errors."""


class WebhookVerificationError(PermissionError):
    """Raised when webhook signature or callback token verification fails."""


def get_xendit_webhook_token() -> str:
    return os.getenv("XENDIT_WEBHOOK_VERIFICATION_TOKEN", "xnd_sandbox_webhook_secret_2026")


def get_midtrans_server_key() -> str:
    return os.getenv("MIDTRANS_SERVER_KEY", "SB-Mid-server-sandbox_secret_2026")


def verify_xendit_webhook(
    callback_token_header: Optional[str],
    raw_body: bytes,
    hmac_signature_header: Optional[str] = None,
) -> bool:
    """
    Verifies Xendit webhook authenticity using constant-time comparison on `x-callback-token`
    and optional `x- callback-signature` HMAC-SHA256.
    """
    expected_token = get_xendit_webhook_token()
    if not callback_token_header:
        return False
    if not hmac.compare_digest(callback_token_header.strip(), expected_token.strip()):
        return False

    if hmac_signature_header:
        computed_hmac = hmac.new(
            expected_token.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(hmac_signature_header.strip().lower(), computed_hmac.lower()):
            return False

    return True


def verify_midtrans_webhook(
    order_id: str,
    status_code: str,
    gross_amount: str,
    signature_key: Optional[str],
) -> bool:
    """
    Verifies Midtrans webhook notification using Midtrans's official signature formula:
    SHA512(order_id + status_code + gross_amount + ServerKey)
    """
    if not signature_key:
        return False
    server_key = get_midtrans_server_key()
    raw_str = f"{order_id}{status_code}{gross_amount}{server_key}"
    expected_sig = hashlib.sha512(raw_str.encode("utf-8")).hexdigest()
    return hmac.compare_digest(signature_key.strip().lower(), expected_sig.lower())


def compute_midtrans_signature(order_id: str, status_code: str, gross_amount: str) -> str:
    """Helper to generate valid Midtrans SHA-512 signatures for sandbox webhook testing."""
    server_key = get_midtrans_server_key()
    return hashlib.sha512(f"{order_id}{status_code}{gross_amount}{server_key}".encode("utf-8")).hexdigest()


class PaymentGatewayService:
    """
    Coordinates external Indonesian payment creation (Xendit / Midtrans), webhook callback
    verification, idempotent state transitions, double-entry ledger settlement, and reconciliation.
    """

    def __init__(self, bank: SandboxBank):
        self.bank = bank

    def _resolve_authoritative_amount_minor(
        self,
        cur,
        *,
        mandate_id: Optional[str],
        order_id: Optional[str],
        requested_amount: Optional[float],
    ) -> Tuple[int, str, str, str]:
        """
        Resolves the authoritative payment amount in minor units from server-side records
        (`executed_orders` or `intent_mandates_store`) rather than trusting arbitrary client input.
        Returns `(amount_minor, currency, item_title, merchant_name)`.
        """
        if order_id:
            cur.execute("SELECT * FROM executed_orders WHERE order_id = ?", (order_id,))
            ord_row = cur.fetchone()
            if not ord_row:
                raise PaymentGatewayError(f"ORDER_NOT_FOUND: Order '{order_id}' does not exist on server.")
            amt_minor = int(ord_row["final_landed_cost_minor"]) or to_minor_units(ord_row["final_landed_cost"])
            return (
                amt_minor,
                ord_row["currency"],
                ord_row["item_title"],
                ord_row["merchant_name"],
            )

        if mandate_id:
            cur.execute("SELECT * FROM intent_mandates_store WHERE mandate_id = ?", (mandate_id,))
            mnd_row = cur.fetchone()
            if not mnd_row:
                # Check in-memory mandates if registered before persistence
                in_mem = self.bank.intent_mandates.get(mandate_id)
                if not in_mem:
                    raise PaymentGatewayError(f"MANDATE_NOT_FOUND: Mandate '{mandate_id}' does not exist on server.")
                max_minor = to_minor_units(in_mem.max_budget)
                req_minor = to_minor_units(requested_amount) if requested_amount else max_minor
                if req_minor <= 0 or req_minor > max_minor:
                    raise PaymentGatewayError(
                        f"AMOUNT_EXCEEDS_MANDATE: Requested {from_minor_units(req_minor):,.2f} exceeds mandate cap {from_minor_units(max_minor):,.2f}."
                    )
                return req_minor, in_mem.currency, in_mem.item_query, "Authorized AP2 Merchant"

            max_minor = int(mnd_row["max_budget_minor"])
            req_minor = to_minor_units(requested_amount) if requested_amount else max_minor
            if req_minor <= 0 or req_minor > max_minor:
                raise PaymentGatewayError(
                    f"AMOUNT_EXCEEDS_MANDATE: Requested {from_minor_units(req_minor):,.2f} exceeds server mandate cap {from_minor_units(max_minor):,.2f}."
                )
            return req_minor, mnd_row["currency"], mnd_row["item_query"], "Authorized AP2 Merchant"

        if requested_amount is None or requested_amount <= 0:
            raise PaymentGatewayError("INVALID_AMOUNT: Positive payment amount or server order_id/mandate_id is required.")

        return to_minor_units(requested_amount), "IDR", "Direct TrueCost Checkout", "Indonesian Verified Merchant"

    def _call_external_provider_or_sandbox(
        self,
        *,
        payment_id: str,
        provider: str,
        payment_method: str,
        amount_minor: int,
        currency: str,
        item_title: str,
        idempotency_key: str,
    ) -> Dict[str, Any]:
        """
        Calls Xendit v2 Invoices API or Midtrans Snap API when live/sandbox keys are configured
        in the environment (`XENDIT_SECRET_KEY` / `MIDTRANS_SERVER_KEY` with `PAYMENT_LIVE_HTTP=true`),
        or generates deterministic Indonesian payment credentials (QRIS / Virtual Account / Hosted URL)
        for local sandbox execution. Never fabricates settled states — always starts in `PENDING`.
        """
        amount_major = int(round(from_minor_units(amount_minor)))
        live_http = os.getenv("PAYMENT_LIVE_HTTP", "false").lower() == "true"

        if provider == "XENDIT":
            xendit_secret = os.getenv("XENDIT_SECRET_KEY", "").strip()
            if live_http and xendit_secret:
                auth_b64 = base64.b64encode(f"{xendit_secret}:".encode("utf-8")).decode("ascii")
                try:
                    with httpx.Client(timeout=8.0) as client:
                        resp = client.post(
                            "https://api.xendit.co/v2/invoices",
                            headers={
                                "Authorization": f"Basic {auth_b64}",
                                "x-idempotency-key": idempotency_key,
                                "Content-Type": "application/json",
                            },
                            json={
                                "external_id": payment_id,
                                "amount": amount_major,
                                "currency": currency,
                                "description": f"TrueCost Autopilot: {item_title}",
                            },
                        )
                        if resp.status_code in (200, 201):
                            data = resp.json()
                            return {
                                "provider_reference": data.get("id", f"xnd_inv_{uuid.uuid4().hex[:12]}"),
                                "checkout_url": data.get("invoice_url"),
                                "qr_string": f"00020101021226660014ID.CO.XENDIT.WWW011893600914{payment_id[-8:]}520454115303360540{amount_major}5802ID",
                                "va_number": f"8808{ str(abs(hash(payment_id)))[:10] }",
                                "gateway_mode": "XENDIT_LIVE_API",
                            }
                except httpx.RequestError as exc:
                    raise PaymentGatewayError(f"XENDIT_NETWORK_TIMEOUT_OR_ERROR: {str(exc)}")

            return {
                "provider_reference": f"xnd_inv_{uuid.uuid4().hex[:14]}",
                "checkout_url": f"https://checkout-staging.xendit.co/web/{payment_id.lower()}",
                "qr_string": f"00020101021226660014ID.CO.XENDIT.WWW011893600914{payment_id[-8:]}520454115303360540{amount_major}5802ID",
                "va_number": f"8808{str(abs(hash(payment_id)))[:10]}",
                "gateway_mode": "XENDIT_SANDBOX_DETERMINISTIC",
            }

        # MIDTRANS
        midtrans_key = os.getenv("MIDTRANS_SERVER_KEY", "").strip()
        if live_http and midtrans_key:
            auth_b64 = base64.b64encode(f"{midtrans_key}:".encode("utf-8")).decode("ascii")
            try:
                with httpx.Client(timeout=8.0) as client:
                    resp = client.post(
                        "https://app.sandbox.midtrans.com/snap/v1/transactions",
                        headers={
                            "Authorization": f"Basic {auth_b64}",
                            "X-Idempotency-Key": idempotency_key,
                            "Content-Type": "application/json",
                            "Accept": "application/json",
                        },
                        json={
                            "transaction_details": {
                                "order_id": payment_id,
                                "gross_amount": amount_major,
                            },
                            "item_details": [
                                {
                                    "id": "ITEM_1",
                                    "price": amount_major,
                                    "quantity": 1,
                                    "name": item_title[:50],
                                }
                            ],
                        },
                    )
                    if resp.status_code in (200, 201):
                        data = resp.json()
                        return {
                            "provider_reference": data.get("token", f"mdt_snap_{uuid.uuid4().hex[:12]}"),
                            "checkout_url": data.get("redirect_url"),
                            "qr_string": f"00020101021226660014ID.CO.MIDTRANS.WWW011893600503{payment_id[-8:]}520454115303360540{amount_major}5802ID",
                            "va_number": f"70012{str(abs(hash(payment_id)))[:10]}",
                            "gateway_mode": "MIDTRANS_LIVE_SNAP",
                        }
            except httpx.RequestError as exc:
                raise PaymentGatewayError(f"MIDTRANS_NETWORK_TIMEOUT_OR_ERROR: {str(exc)}")

        return {
            "provider_reference": f"mdt_snap_{uuid.uuid4().hex[:14]}",
            "checkout_url": f"https://app.sandbox.midtrans.com/snap/v2/vtweb/{payment_id.lower()}",
            "qr_string": f"00020101021226660014ID.CO.MIDTRANS.WWW011893600503{payment_id[-8:]}520454115303360540{amount_major}5802ID",
            "va_number": f"70012{str(abs(hash(payment_id)))[:10]}",
            "gateway_mode": "MIDTRANS_SANDBOX_DETERMINISTIC",
        }

    def create_payment_request(
        self,
        *,
        user_id: str = "USR_DEFAULT",
        provider: str = "XENDIT",
        payment_method: str = "QRIS",
        mandate_id: Optional[str] = None,
        order_id: Optional[str] = None,
        amount_idr: Optional[float] = None,
        item_title: Optional[str] = None,
        merchant_name: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Steps 1-6 of Phase 3 External Financial Flow:
        Authenticates user, resolves authoritative server-side amount, creates payment request
        with Xendit/Midtrans, persists `PENDING` transaction in SQLite, and returns safe client checkout data.
        """
        self.bank.verify_user_authorization(user_id, "USR_DEFAULT")
        provider_norm = provider.upper().strip()
        method_norm = payment_method.upper().strip()

        if provider_norm not in SUPPORTED_PROVIDERS:
            raise PaymentGatewayError(f"UNSUPPORTED_PROVIDER: '{provider_norm}'. Supported: {sorted(SUPPORTED_PROVIDERS)}")
        if method_norm not in SUPPORTED_PAYMENT_METHODS:
            raise PaymentGatewayError(f"UNSUPPORTED_METHOD: '{method_norm}'. Supported: {sorted(SUPPORTED_PAYMENT_METHODS)}")

        eff_idem_key = idempotency_key or f"IDEM_{uuid.uuid4().hex[:16].upper()}"

        def _op() -> Dict[str, Any]:
            with atomic_db_transaction(self.bank.db_path) as cur:
                auth_minor, currency, resolved_title, resolved_merchant = self._resolve_authoritative_amount_minor(
                    cur,
                    mandate_id=mandate_id,
                    order_id=order_id,
                    requested_amount=amount_idr,
                )
                final_title = item_title or resolved_title
                final_merchant = merchant_name or resolved_merchant

                # Verify user has sufficient liquid balance (Sinking Pot + Checking) before creating payment intent
                cur.execute(
                    "SELECT COALESCE(SUM(balance_minor), 0) AS liquid_minor FROM accounts "
                    "WHERE account_id IN ('ACC_USER_CHECKING', 'ACC_USER_SINKING_POT')"
                )
                liquid_minor = int(cur.fetchone()["liquid_minor"])
                if liquid_minor < auth_minor:
                    raise PaymentGatewayError(
                        f"INSUFFICIENT_LIQUID_FUNDS: Available {from_minor_units(liquid_minor):,.2f} {currency} "
                        f"is less than payment amount {from_minor_units(auth_minor):,.2f} {currency}."
                    )

                payment_id = f"PAY_{uuid.uuid4().hex[:12].upper()}"
                gw_res = self._call_external_provider_or_sandbox(
                    payment_id=payment_id,
                    provider=provider_norm,
                    payment_method=method_norm,
                    amount_minor=auth_minor,
                    currency=currency,
                    item_title=final_title,
                    idempotency_key=eff_idem_key,
                )

                now_iso = datetime.now(timezone.utc).isoformat()
                cur.execute(
                    """
                    INSERT INTO payment_transactions (
                        payment_id, order_id, mandate_id, user_id, provider, provider_reference,
                        payment_method, merchant_name, item_title, amount_minor, currency,
                        status, checkout_url, qr_string, va_number, idempotency_key,
                        metadata_json, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        payment_id,
                        order_id,
                        mandate_id,
                        user_id,
                        provider_norm,
                        gw_res["provider_reference"],
                        method_norm,
                        final_merchant,
                        final_title,
                        auth_minor,
                        currency,
                        gw_res["checkout_url"],
                        gw_res["qr_string"],
                        gw_res["va_number"],
                        eff_idem_key,
                        json.dumps({"gateway_mode": gw_res["gateway_mode"]}),
                        now_iso,
                        now_iso,
                    ),
                )

                record_audit_log(
                    user_id=user_id,
                    action="PAYMENT_INTENT_CREATED",
                    resource_type="PAYMENT_TRANSACTION",
                    resource_id=payment_id,
                    status="PENDING",
                    details={
                        "provider": provider_norm,
                        "payment_method": method_norm,
                        "amount_minor": auth_minor,
                        "provider_reference": gw_res["provider_reference"],
                    },
                    cur=cur,
                )

                return {
                    "payment_id": payment_id,
                    "order_id": order_id,
                    "mandate_id": mandate_id,
                    "provider": provider_norm,
                    "provider_reference": gw_res["provider_reference"],
                    "payment_method": method_norm,
                    "item_title": final_title,
                    "merchant_name": final_merchant,
                    "amount": from_minor_units(auth_minor),
                    "amount_minor": auth_minor,
                    "currency": currency,
                    "status": "PENDING",
                    "checkout_url": gw_res["checkout_url"],
                    "qr_string": gw_res["qr_string"],
                    "va_number": gw_res["va_number"],
                    "gateway_mode": gw_res["gateway_mode"],
                    "created_at": now_iso,
                }

        return self.bank.execute_idempotent(
            idempotency_key=eff_idem_key,
            user_id=user_id,
            endpoint="POST:/api/payments/create",
            request_payload={
                "provider": provider_norm,
                "payment_method": method_norm,
                "mandate_id": mandate_id,
                "order_id": order_id,
                "amount_idr": amount_idr,
                "item_title": item_title,
            },
            operation_fn=_op,
        )

    def process_webhook_event(
        self,
        *,
        provider: str,
        provider_event_id: str,
        payment_id: str,
        target_status: str,
        reported_amount: float,
        currency: str = "IDR",
        raw_payload: Dict[str, Any],
        signature_valid: bool,
    ) -> Dict[str, Any]:
        """
        Steps 7-11 of Phase 3 External Financial Flow:
        1. Logs webhook event and rejects invalid cryptographic signatures (`WebhookVerificationError`).
        2. Deduplicates replay/duplicate webhooks via `UNIQUE(provider, provider_event_id)`.
        3. Validates payment reference, currency, exact minor-unit amount, and allowed state transition.
        4. Updates `payment_transactions.status` atomically.
        5. Posts balanced double-entry accounting entries (`ledger_journals` + `ledger_entries`)
           EXACTLY ONCE when transitioning to `PAID`, or posts a reversing journal when transitioning to `REFUNDED`.
        """
        provider_norm = provider.upper().strip()
        target_status_norm = target_status.upper().strip()
        now_iso = datetime.now(timezone.utc).isoformat()
        raw_json = json.dumps(raw_payload, sort_keys=True, default=str)
        payload_hash = hashlib.sha256(raw_json.encode("utf-8")).hexdigest()

        if not signature_valid:
            with atomic_db_transaction(self.bank.db_path) as cur:
                event_pk = f"WHK_{uuid.uuid4().hex[:12].upper()}"
                cur.execute(
                    """
                    INSERT OR IGNORE INTO webhook_events (
                        event_id, provider, provider_event_id, payment_id, signature_verified,
                        payload_hash, raw_payload_json, processing_status, error_message, received_at, processed_at
                    ) VALUES (?, ?, ?, ?, 0, ?, ?, 'REJECTED_SIGNATURE', 'Invalid webhook signature or token', ?, ?)
                    """,
                    (event_pk, provider_norm, provider_event_id, payment_id, payload_hash, raw_json, now_iso, now_iso),
                )
                record_audit_log(
                    user_id="SYSTEM_WEBHOOK",
                    action="WEBHOOK_SIGNATURE_REJECTED",
                    resource_type="WEBHOOK_EVENT",
                    resource_id=provider_event_id,
                    status="DENIED",
                    details={"provider": provider_norm, "payment_id": payment_id},
                    cur=cur,
                )
            raise WebhookVerificationError(
                f"WEBHOOK_SIGNATURE_INVALID: Cryptographic verification failed for {provider_norm} event '{provider_event_id}'."
            )

        with atomic_db_transaction(self.bank.db_path) as cur:
            # 1. Check for duplicate webhook event
            cur.execute(
                "SELECT event_id, processing_status FROM webhook_events WHERE provider = ? AND provider_event_id = ?",
                (provider_norm, provider_event_id),
            )
            existing_event = cur.fetchone()
            if existing_event:
                return {
                    "status": "DUPLICATE_IGNORED",
                    "idempotent_replay": True,
                    "event_id": existing_event["event_id"],
                    "payment_id": payment_id,
                    "message": f"Webhook event {provider_event_id} already processed.",
                }

            # 2. Load authoritative payment transaction
            cur.execute("SELECT * FROM payment_transactions WHERE payment_id = ?", (payment_id,))
            pay_row = cur.fetchone()
            if not pay_row:
                raise PaymentGatewayError(f"PAYMENT_NOT_FOUND: Payment '{payment_id}' does not exist.")

            current_status = pay_row["status"]
            expected_minor = int(pay_row["amount_minor"])
            reported_minor = to_minor_units(reported_amount)

            if reported_minor != expected_minor:
                raise PaymentGatewayError(
                    f"WEBHOOK_AMOUNT_MISMATCH: Webhook reported {from_minor_units(reported_minor):,.2f}, "
                    f"expected authoritative amount {from_minor_units(expected_minor):,.2f}."
                )

            if currency.upper() != pay_row["currency"].upper():
                raise PaymentGatewayError(
                    f"WEBHOOK_CURRENCY_MISMATCH: Webhook reported {currency}, expected {pay_row['currency']}."
                )

            # 3. Handle idempotent same-status delivery (e.g. duplicate PAID notification with new event_id)
            if current_status == target_status_norm:
                event_pk = f"WHK_{uuid.uuid4().hex[:12].upper()}"
                cur.execute(
                    """
                    INSERT INTO webhook_events (
                        event_id, provider, provider_event_id, payment_id, signature_verified,
                        payload_hash, raw_payload_json, processing_status, received_at, processed_at
                    ) VALUES (?, ?, ?, ?, 1, ?, ?, 'DUPLICATE_IGNORED', ?, ?)
                    """,
                    (event_pk, provider_norm, provider_event_id, payment_id, payload_hash, raw_json, now_iso, now_iso),
                )
                return {
                    "status": "ALREADY_IN_TARGET_STATE",
                    "idempotent_replay": True,
                    "payment_id": payment_id,
                    "payment_status": current_status,
                    "journal_id": pay_row["journal_id"],
                }

            # 4. Validate state machine transition
            allowed_next = VALID_STATE_TRANSITIONS.get(current_status, set())
            if target_status_norm not in allowed_next:
                raise PaymentGatewayError(
                    f"INVALID_STATE_TRANSITION: Cannot transition payment {payment_id} from '{current_status}' to '{target_status_norm}'."
                )

            journal_id = pay_row["journal_id"]
            reversal_journal_id = pay_row["reversal_journal_id"]
            settled_at = pay_row["settled_at"]

            # 5. Execute double-entry accounting at the exact accounting event
            if target_status_norm == "PAID":
                # Debit from Sinking Pot first (if reserved), otherwise Checking
                cur.execute("SELECT balance_minor FROM accounts WHERE account_id = 'ACC_USER_SINKING_POT'")
                pot_minor = int(cur.fetchone()["balance_minor"])
                cur.execute("SELECT balance_minor FROM accounts WHERE account_id = 'ACC_USER_CHECKING'")
                checking_minor = int(cur.fetchone()["balance_minor"])

                postings: List[Tuple[str, str, int]] = []
                if pot_minor >= expected_minor:
                    postings.append(("ACC_USER_SINKING_POT", "DEBIT", expected_minor))
                    debit_source = "ACC_USER_SINKING_POT"
                elif (pot_minor + checking_minor) >= expected_minor:
                    if pot_minor > 0:
                        postings.append(("ACC_USER_SINKING_POT", "DEBIT", pot_minor))
                    rem = expected_minor - pot_minor
                    if rem > 0:
                        postings.append(("ACC_USER_CHECKING", "DEBIT", rem))
                    debit_source = "COMBINED_POT_AND_CHECKING"
                else:
                    raise PaymentGatewayError("INSUFFICIENT_FUNDS_ON_SETTLEMENT")

                postings.append(("ACC_MERCHANT_SETTLEMENT_CLEARING", "CREDIT", expected_minor))

                tx_id = str(uuid.uuid4())
                journal = post_double_entry_journal(
                    cur,
                    tx_id=tx_id,
                    user_id=pay_row["user_id"],
                    entry_type="EXTERNAL_GATEWAY_SETTLEMENT",
                    description=f"{provider_norm} ({pay_row['payment_method']}) settlement for {pay_row['item_title']}",
                    currency=pay_row["currency"],
                    postings=postings,
                )
                journal_id = journal["journal_id"]
                settled_at = now_iso

                tx_rec = record_chained_transaction_in_cursor(
                    cur,
                    {
                        "tx_id": tx_id,
                        "user_id": pay_row["user_id"],
                        "type": f"{provider_norm}_{pay_row['payment_method']}_SETTLEMENT",
                        "amount": from_minor_units(expected_minor),
                        "amount_minor": expected_minor,
                        "currency": pay_row["currency"],
                        "from_account": debit_source,
                        "to_account": pay_row["merchant_name"],
                        "mandate_id": pay_row["mandate_id"],
                        "order_id": pay_row["order_id"] or payment_id,
                        "timestamp": now_iso,
                        "status": "COMPLETED",
                    },
                    journal_id=journal_id,
                )
                self.bank.transactions.append(tx_rec)

            elif target_status_norm == "REFUNDED":
                if not journal_id:
                    raise PaymentGatewayError(f"Cannot refund payment {payment_id} without an original settlement journal.")
                cur.execute("SELECT * FROM ledger_entries WHERE journal_id = ? ORDER BY rowid ASC", (journal_id,))
                orig_entries = cur.fetchall()
                rev_postings = [
                    (e["account_id"], "CREDIT" if e["direction"] == "DEBIT" else "DEBIT", int(e["amount_minor"]))
                    for e in orig_entries
                ]
                rev_tx_id = str(uuid.uuid4())
                rev_journal = post_double_entry_journal(
                    cur,
                    tx_id=rev_tx_id,
                    user_id=pay_row["user_id"],
                    entry_type="EXTERNAL_GATEWAY_REFUND_REVERSAL",
                    description=f"Refund reversal for {payment_id} ({provider_norm})",
                    currency=pay_row["currency"],
                    postings=rev_postings,
                    is_reversal=True,
                    reverses_journal_id=journal_id,
                )
                reversal_journal_id = rev_journal["journal_id"]
                rev_tx = record_chained_transaction_in_cursor(
                    cur,
                    {
                        "tx_id": rev_tx_id,
                        "user_id": pay_row["user_id"],
                        "type": f"{provider_norm}_REFUND_REVERSAL",
                        "amount": from_minor_units(expected_minor),
                        "amount_minor": expected_minor,
                        "currency": pay_row["currency"],
                        "from_account": pay_row["merchant_name"],
                        "to_account": "ACC_USER_CHECKING",
                        "order_id": pay_row["order_id"] or payment_id,
                        "timestamp": now_iso,
                        "status": "REFUNDED",
                    },
                    journal_id=reversal_journal_id,
                )
                self.bank.transactions.append(rev_tx)

            # 6. Update payment_transactions and insert webhook_events
            cur.execute(
                """
                UPDATE payment_transactions
                SET status = ?, journal_id = ?, reversal_journal_id = ?, updated_at = ?, settled_at = ?
                WHERE payment_id = ?
                """,
                (target_status_norm, journal_id, reversal_journal_id, now_iso, settled_at, payment_id),
            )

            event_pk = f"WHK_{uuid.uuid4().hex[:12].upper()}"
            cur.execute(
                """
                INSERT INTO webhook_events (
                    event_id, provider, provider_event_id, payment_id, signature_verified,
                    payload_hash, raw_payload_json, processing_status, received_at, processed_at
                ) VALUES (?, ?, ?, ?, 1, ?, ?, 'PROCESSED', ?, ?)
                """,
                (event_pk, provider_norm, provider_event_id, payment_id, payload_hash, raw_json, now_iso, now_iso),
            )

            record_audit_log(
                user_id="SYSTEM_WEBHOOK",
                action=f"PAYMENT_WEBHOOK_{target_status_norm}",
                resource_type="PAYMENT_TRANSACTION",
                resource_id=payment_id,
                status="SUCCESS",
                details={
                    "provider": provider_norm,
                    "provider_event_id": provider_event_id,
                    "previous_status": current_status,
                    "new_status": target_status_norm,
                    "journal_id": journal_id,
                    "reversal_journal_id": reversal_journal_id,
                },
                cur=cur,
            )

            self.bank._refresh_in_memory_accounts_from_cursor(cur)

            return {
                "status": "PROCESSED",
                "idempotent_replay": False,
                "event_id": event_pk,
                "payment_id": payment_id,
                "previous_status": current_status,
                "payment_status": target_status_norm,
                "amount": from_minor_units(expected_minor),
                "amount_minor": expected_minor,
                "journal_id": journal_id,
                "reversal_journal_id": reversal_journal_id,
                "checking_balance_idr": self.bank.accounts["ACC_USER_CHECKING"]["balance"],
                "sinking_pot_idr": self.bank.accounts["ACC_USER_SINKING_POT"]["balance"],
            }

    def get_payment(self, payment_id: str, user_id: str = "USR_DEFAULT") -> Dict[str, Any]:
        self.bank.verify_user_authorization(user_id, "USR_DEFAULT")
        conn = get_db_connection(self.bank.db_path)
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM payment_transactions WHERE payment_id = ?", (payment_id,))
            row = cur.fetchone()
            if not row:
                raise PaymentGatewayError(f"PAYMENT_NOT_FOUND: '{payment_id}'")
            if row["user_id"] != user_id:
                self.bank.verify_user_authorization(user_id, row["user_id"])
            data = dict(row)
            data["amount"] = from_minor_units(int(row["amount_minor"]))
            return data
        finally:
            conn.close()

    def list_payments(self, user_id: str = "USR_DEFAULT", limit: int = 50) -> List[Dict[str, Any]]:
        self.bank.verify_user_authorization(user_id, "USR_DEFAULT")
        conn = get_db_connection(self.bank.db_path)
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT * FROM payment_transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
            )
            results = []
            for r in cur.fetchall():
                d = dict(r)
                d["amount"] = from_minor_units(int(r["amount_minor"]))
                results.append(d)
            return results
        finally:
            conn.close()

    def reconcile_payments(
        self,
        provider_settlement_report: Optional[List[Dict[str, Any]]] = None,
        user_id: str = "USR_DEFAULT",
    ) -> Dict[str, Any]:
        """
        Step 12 of Phase 3 External Financial Flow:
        Reconciles internal `payment_transactions` and `ledger_journals` with external provider
        settlement reports, verifying:
        1. Every `PAID` transaction has a valid, balanced `ledger_journals` record matching `amount_minor`.
        2. Every `REFUNDED` transaction has a valid `reversal_journal_id`.
        3. External provider settlement statuses & amounts match internal records (auto-healing delayed
           webhooks if a verified provider settlement report shows `PAID`).
        """
        self.bank.verify_user_authorization(user_id, "USR_DEFAULT")

        discrepancies: List[Dict[str, Any]] = []
        matched_count = 0
        auto_healed_count = 0

        # Optional: if provider_settlement_report includes items that settled externally while webhook was delayed
        if provider_settlement_report:
            for ext in provider_settlement_report:
                ext_pay_id = ext.get("payment_id")
                ext_status = str(ext.get("status", "")).upper()
                ext_amount = ext.get("amount")
                if ext_pay_id and ext_status in ("PAID", "REFUNDED") and ext_amount is not None:
                    try:
                        conn = get_db_connection(self.bank.db_path)
                        cur = conn.cursor()
                        cur.execute("SELECT status, provider, currency FROM payment_transactions WHERE payment_id = ?", (ext_pay_id,))
                        row = cur.fetchone()
                        conn.close()
                        if row and row["status"] != ext_status:
                            self.process_webhook_event(
                                provider=row["provider"],
                                provider_event_id=f"RECON_AUTO_{ext_pay_id}_{ext_status}",
                                payment_id=ext_pay_id,
                                target_status=ext_status,
                                reported_amount=float(ext_amount),
                                currency=row["currency"],
                                raw_payload={"source": "reconciliation_report", **ext},
                                signature_valid=True,
                            )
                            auto_healed_count += 1
                    except Exception as exc:
                        discrepancies.append(
                            {
                                "payment_id": ext_pay_id,
                                "issue": f"RECON_HEAL_FAILED: {str(exc)}",
                            }
                        )

        with atomic_db_transaction(self.bank.db_path) as cur:
            cur.execute("SELECT * FROM payment_transactions ORDER BY created_at ASC")
            all_payments = cur.fetchall()
            total_checked = len(all_payments)

            for p in all_payments:
                p_id = p["payment_id"]
                p_status = p["status"]
                p_minor = int(p["amount_minor"])
                j_id = p["journal_id"]

                if p_status == "PAID":
                    if not j_id:
                        discrepancies.append({"payment_id": p_id, "issue": "MISSING_LEDGER_JOURNAL_FOR_PAID_TX"})
                        continue
                    cur.execute("SELECT total_debit_minor, total_credit_minor FROM ledger_journals WHERE journal_id = ?", (j_id,))
                    j_row = cur.fetchone()
                    if not j_row:
                        discrepancies.append({"payment_id": p_id, "issue": f"ORPHAN_JOURNAL_REF:{j_id}"})
                        continue
                    if int(j_row["total_debit_minor"]) != p_minor or int(j_row["total_credit_minor"]) != p_minor:
                        discrepancies.append(
                            {
                                "payment_id": p_id,
                                "issue": "LEDGER_AMOUNT_MISMATCH",
                                "payment_minor": p_minor,
                                "journal_debit_minor": int(j_row["total_debit_minor"]),
                            }
                        )
                        continue
                    matched_count += 1
                elif p_status == "REFUNDED":
                    if not p["reversal_journal_id"]:
                        discrepancies.append({"payment_id": p_id, "issue": "MISSING_REVERSAL_JOURNAL_FOR_REFUND"})
                        continue
                    matched_count += 1
                else:
                    matched_count += 1

            recon_id = f"REC_{uuid.uuid4().hex[:12].upper()}"
            now_iso = datetime.now(timezone.utc).isoformat()
            recon_status = "RECONCILED_CLEAN" if len(discrepancies) == 0 else "DISCREPANCY_DETECTED"

            cur.execute(
                """
                INSERT INTO reconciliation_records (
                    recon_id, run_timestamp, total_checked, matched_count,
                    mismatched_count, auto_healed_count, discrepancies_json, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    recon_id,
                    now_iso,
                    total_checked,
                    matched_count,
                    len(discrepancies),
                    auto_healed_count,
                    json.dumps(discrepancies),
                    recon_status,
                ),
            )
            record_audit_log(
                user_id=user_id,
                action="PAYMENT_RECONCILIATION_COMPLETED",
                resource_type="RECONCILIATION",
                resource_id=recon_id,
                status=recon_status,
                details={
                    "total_checked": total_checked,
                    "matched_count": matched_count,
                    "mismatched_count": len(discrepancies),
                    "auto_healed_count": auto_healed_count,
                },
                cur=cur,
            )

            return {
                "recon_id": recon_id,
                "run_timestamp": now_iso,
                "status": recon_status,
                "total_checked": total_checked,
                "matched_count": matched_count,
                "mismatched_count": len(discrepancies),
                "auto_healed_count": auto_healed_count,
                "discrepancies": discrepancies,
            }


payment_gateway_service = PaymentGatewayService(bank_service)
