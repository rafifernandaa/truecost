import os
import sqlite3
import tempfile
import uuid
import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from app.main import app, reset_rate_limiter
from app.bank.database import (
    atomic_db_transaction,
    from_minor_units,
    get_db_connection,
    init_bank_db,
    post_double_entry_journal,
    to_minor_units,
)
from app.bank.service import (
    IdempotencyConflictError,
    SandboxBank,
    UnauthorizedResourceAccessError,
)
from app.bank.payment_gateway import (
    PaymentGatewayError,
    PaymentGatewayService,
    WebhookVerificationError,
    compute_midtrans_signature,
    get_xendit_webhook_token,
)


@pytest.fixture
def temp_db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


@pytest.fixture
def isolated_bank(temp_db_path):
    reset_rate_limiter()
    return SandboxBank(persist_state=True, db_path=temp_db_path)


@pytest.fixture
def isolated_gateway(isolated_bank):
    return PaymentGatewayService(isolated_bank)


def test_minor_unit_decimal_precision_no_float_drift():
    """
    Verifies monetary conversion uses exact Decimal arithmetic and never suffers IEEE 754 float drift.
    """
    a = to_minor_units("0.10")
    b = to_minor_units("0.20")
    assert a + b == 30
    assert from_minor_units(a + b) == 0.30

    idr_val = to_minor_units(15820000.55)
    assert idr_val == 1582000055
    assert from_minor_units(idr_val) == 15820000.55


def test_schema_migrations_and_state_persistence_across_restarts(temp_db_path):
    """
    Verifies versioned schema migrations run cleanly and balances/transactions persist across restarts.
    """
    bank1 = SandboxBank(persist_state=True, db_path=temp_db_path)
    conn = get_db_connection(temp_db_path)
    cur = conn.cursor()
    cur.execute("SELECT version FROM schema_migrations ORDER BY version ASC")
    versions = [r["version"] for r in cur.fetchall()]
    conn.close()
    assert versions == [1, 2, 3]

    dep = bank1.deposit_income(5_000_000.0, source="Scholarship Stipend")
    assert dep["checking_balance_idr"] == 29_000_000.0
    assert dep["emergency_buffer_idr"] == 11_000_000.0

    # Simulate server restart by instantiating a new SandboxBank pointing at the same SQLite DB
    bank2 = SandboxBank(persist_state=True, db_path=temp_db_path)
    summary = bank2.get_account_summary()
    assert summary["checking_balance_idr"] == 29_000_000.0
    assert summary["emergency_buffer_idr"] == 11_000_000.0
    assert len(bank2.transactions) == 1


def test_double_entry_ledger_balancing_and_unbalanced_rejection(isolated_bank, temp_db_path):
    """
    Verifies every financial operation produces balanced DEBIT == CREDIT entries and rejects unbalanced postings.
    """
    isolated_bank.deposit_income(10_000_000.0, source="Salary")
    isolated_bank.execute_real_case_flow(
        item_title="Samsung Galaxy A57",
        max_budget_idr=7_000_000.0,
        optimal_landed_idr=6_450_000.0,
        mode="reserve_and_settle",
    )

    ledger = isolated_bank.get_ledger_summary()
    assert ledger["is_balanced"] is True
    assert ledger["total_debit_minor"] == ledger["total_credit_minor"]
    assert ledger["total_debit_minor"] > 0

    # Attempt to post an unbalanced journal -> must fail
    with pytest.raises(ValueError, match="UNBALANCED_JOURNAL"):
        with atomic_db_transaction(temp_db_path) as cur:
            post_double_entry_journal(
                cur,
                tx_id=str(uuid.uuid4()),
                user_id="USR_DEFAULT",
                entry_type="CORRUPT_TEST",
                description="Unbalanced test",
                currency="IDR",
                postings=[
                    ("ACC_USER_CHECKING", "DEBIT", 500_00),
                    ("ACC_USER_SINKING_POT", "CREDIT", 400_00),
                ],
            )


def test_ledger_entries_and_audit_logs_are_immutable_with_reversing_journal_support(isolated_bank, temp_db_path):
    """
    Verifies SQLite triggers block UPDATE/DELETE on posted ledger_entries and audit_logs,
    and corrections use reversing journals instead.
    """
    dep = isolated_bank.deposit_income(2_000_000.0, source="Bonus")
    journal_id = dep["journal_id"]

    conn = get_db_connection(temp_db_path)
    cur = conn.cursor()
    with pytest.raises(sqlite3.IntegrityError, match="IMMUTABLE_LEDGER_VIOLATION"):
        cur.execute("UPDATE ledger_entries SET amount_minor = 999 WHERE journal_id = ?", (journal_id,))
    with pytest.raises(sqlite3.IntegrityError, match="IMMUTABLE_LEDGER_VIOLATION"):
        cur.execute("DELETE FROM ledger_entries WHERE journal_id = ?", (journal_id,))
    with pytest.raises(sqlite3.IntegrityError, match="IMMUTABLE_AUDIT_VIOLATION"):
        cur.execute("DELETE FROM audit_logs")
    conn.close()

    # Now reverse the journal properly via reverse_journal()
    rev = isolated_bank.reverse_journal(journal_id, reason="Duplicate payroll correction")
    assert rev["status"] == "REVERSED"
    summary = isolated_bank.get_account_summary()
    assert summary["checking_balance_idr"] == 25_000_000.0
    assert summary["emergency_buffer_idr"] == 10_000_000.0

    ledger = isolated_bank.get_ledger_summary()
    assert ledger["is_balanced"] is True


def test_atomic_transaction_rollback_on_mid_flight_failure(isolated_bank, temp_db_path):
    """
    Verifies that if an error occurs mid-transaction, all database writes roll back atomically.
    """
    initial_checking = isolated_bank.get_account_summary()["checking_balance_minor"]

    with pytest.raises(RuntimeError, match="SIMULATED_CRASH"):
        with atomic_db_transaction(temp_db_path) as cur:
            post_double_entry_journal(
                cur,
                tx_id=str(uuid.uuid4()),
                user_id="USR_DEFAULT",
                entry_type="TEST_ROLLBACK",
                description="Should roll back",
                currency="IDR",
                postings=[
                    ("ACC_USER_CHECKING", "DEBIT", 1_000_000_00),
                    ("ACC_USER_SINKING_POT", "CREDIT", 1_000_000_00),
                ],
            )
            raise RuntimeError("SIMULATED_CRASH")

    after_checking = isolated_bank.get_account_summary()["checking_balance_minor"]
    assert after_checking == initial_checking


def test_idempotency_key_prevents_duplicate_execution_and_detects_payload_conflict(isolated_bank):
    """
    Verifies Idempotency-Key deduplicates identical retries and rejects conflicting payloads.
    """
    idem_key = "IDEM_TEST_DEPOSIT_001"
    res1 = isolated_bank.deposit_income(5_000_000.0, source="Freelance", idempotency_key=idem_key)
    assert res1["idempotent_replay"] is False
    assert res1["checking_balance_idr"] == 29_000_000.0

    # Retry with same key and same payload -> returns cached result without crediting twice
    res2 = isolated_bank.deposit_income(5_000_000.0, source="Freelance", idempotency_key=idem_key)
    assert res2["idempotent_replay"] is True
    assert isolated_bank.get_account_summary()["checking_balance_idr"] == 29_000_000.0

    # Reuse same key with DIFFERENT amount -> raises IdempotencyConflictError
    with pytest.raises(IdempotencyConflictError, match="IDEMPOTENCY_KEY_CONFLICT"):
        isolated_bank.deposit_income(9_000_000.0, source="Freelance", idempotency_key=idem_key)


def test_xendit_and_midtrans_payment_lifecycle_webhook_signatures_and_idempotency(isolated_gateway, isolated_bank):
    """
    Tests end-to-end payment creation, Xendit & Midtrans webhook signature verification,
    duplicate/out-of-order webhook protection, exactly-once double-entry settlement, and refund reversal.
    """
    # 1. Create Xendit QRIS payment intent
    pay_xnd = isolated_gateway.create_payment_request(
        provider="XENDIT",
        payment_method="QRIS",
        amount_idr=4_500_000.0,
        item_title="Sony WH-1000XM5 Headphones",
        merchant_name="Sony Center Jakarta",
        idempotency_key="IDEM_XND_01",
    )
    assert pay_xnd["status"] == "PENDING"
    payment_id = pay_xnd["payment_id"]

    # Balance should not be debited while PENDING
    assert isolated_bank.get_account_summary()["checking_balance_idr"] == 25_000_000.0

    # 2. Invalid webhook signature must be rejected and logged
    with pytest.raises(WebhookVerificationError, match="WEBHOOK_SIGNATURE_INVALID"):
        isolated_gateway.process_webhook_event(
            provider="XENDIT",
            provider_event_id="EVT_FORGED_01",
            payment_id=payment_id,
            target_status="PAID",
            reported_amount=4_500_000.0,
            currency="IDR",
            raw_payload={"id": "EVT_FORGED_01"},
            signature_valid=False,
        )

    # 3. Valid Xendit PAID webhook settles payment and posts balanced double-entry journal
    res_paid = isolated_gateway.process_webhook_event(
        provider="XENDIT",
        provider_event_id="EVT_XND_VALID_01",
        payment_id=payment_id,
        target_status="PAID",
        reported_amount=4_500_000.0,
        currency="IDR",
        raw_payload={"id": "EVT_XND_VALID_01", "status": "PAID"},
        signature_valid=True,
    )
    assert res_paid["payment_status"] == "PAID"
    assert res_paid["journal_id"] is not None
    assert isolated_bank.get_account_summary()["checking_balance_idr"] == 20_500_000.0

    # 4. Duplicate webhook with same event_id OR new event_id for already-PAID payment is ignored idempotently
    res_dup1 = isolated_gateway.process_webhook_event(
        provider="XENDIT",
        provider_event_id="EVT_XND_VALID_01",
        payment_id=payment_id,
        target_status="PAID",
        reported_amount=4_500_000.0,
        currency="IDR",
        raw_payload={"id": "EVT_XND_VALID_01", "status": "PAID"},
        signature_valid=True,
    )
    assert res_dup1["idempotent_replay"] is True
    assert isolated_bank.get_account_summary()["checking_balance_idr"] == 20_500_000.0

    # 5. Out-of-order / invalid transition (PAID -> EXPIRED) is blocked
    with pytest.raises(PaymentGatewayError, match="INVALID_STATE_TRANSITION"):
        isolated_gateway.process_webhook_event(
            provider="XENDIT",
            provider_event_id="EVT_XND_LATE_EXPIRE",
            payment_id=payment_id,
            target_status="EXPIRED",
            reported_amount=4_500_000.0,
            currency="IDR",
            raw_payload={"id": "EVT_XND_LATE_EXPIRE", "status": "EXPIRED"},
            signature_valid=True,
        )

    # 6. Refund transition (PAID -> REFUNDED) posts reversing journal and restores user balance
    res_refund = isolated_gateway.process_webhook_event(
        provider="XENDIT",
        provider_event_id="EVT_XND_REFUND_01",
        payment_id=payment_id,
        target_status="REFUNDED",
        reported_amount=4_500_000.0,
        currency="IDR",
        raw_payload={"id": "EVT_XND_REFUND_01", "status": "REFUNDED"},
        signature_valid=True,
    )
    assert res_refund["payment_status"] == "REFUNDED"
    assert res_refund["reversal_journal_id"] is not None
    assert isolated_bank.get_account_summary()["checking_balance_idr"] == 25_000_000.0


def test_cross_user_authorization_and_reconciliation(isolated_gateway, isolated_bank):
    """
    Verifies unauthorized users cannot access or mutate records, and reconciliation verifies
    and auto-heals delayed provider settlements.
    """
    with pytest.raises(UnauthorizedResourceAccessError):
        isolated_bank.get_account_summary(user_id="USR_MALLORY_OTHER")

    with pytest.raises(UnauthorizedResourceAccessError):
        isolated_gateway.list_payments(user_id="USR_MALLORY_OTHER")

    # Create a Midtrans Virtual Account payment that remains PENDING due to delayed webhook
    pay_mdt = isolated_gateway.create_payment_request(
        provider="MIDTRANS",
        payment_method="VIRTUAL_ACCOUNT_BCA",
        amount_idr=3_200_000.0,
        item_title="Logitech MX Master 3S",
        merchant_name="Logitech Official ID",
    )
    p_id = pay_mdt["payment_id"]
    assert pay_mdt["status"] == "PENDING"

    # Run reconciliation with a provider settlement report showing MIDTRANS settled p_id
    recon = isolated_gateway.reconcile_payments(
        provider_settlement_report=[
            {"payment_id": p_id, "status": "PAID", "amount": 3_200_000.0}
        ]
    )
    assert recon["status"] == "RECONCILED_CLEAN"
    assert recon["auto_healed_count"] == 1
    assert recon["mismatched_count"] == 0

    updated_pay = isolated_gateway.get_payment(p_id)
    assert updated_pay["status"] == "PAID"
    assert updated_pay["journal_id"] is not None
    assert isolated_bank.get_account_summary()["checking_balance_idr"] == 21_800_000.0


def test_fastapi_payment_webhook_and_security_endpoints():
    """
    End-to-end API integration test for `/api/payments/*`, `/api/webhooks/*`, `/api/bank/ledger`,
    and cross-user 403 protection.
    """
    reset_rate_limiter()
    client = TestClient(app)

    # 1. Cross-user access returns 403 Forbidden
    r_forbidden = client.get("/api/bank/accounts", headers={"X-User-Id": "USR_INTRUDER"})
    assert r_forbidden.status_code == 403

    # 2. Create Midtrans payment via REST endpoint
    r_create = client.post(
        "/api/payments/create",
        headers={"Idempotency-Key": f"API_IDEM_{uuid.uuid4().hex[:8]}"},
        json={
            "provider": "MIDTRANS",
            "payment_method": "QRIS",
            "amount_idr": 1_250_000.0,
            "item_title": "Keychron K2 Pro Mechanical Keyboard",
            "merchant_name": "Keychron Indonesia",
        },
    )
    assert r_create.status_code == 200
    pay_data = r_create.json()
    pay_id = pay_data["payment_id"]
    assert pay_data["status"] == "PENDING"

    # 3. Call Midtrans webhook with forged signature -> 401 Unauthorized
    r_bad_whk = client.post(
        "/api/webhooks/midtrans",
        json={
            "transaction_id": f"evt_bad_{uuid.uuid4().hex[:6]}",
            "order_id": pay_id,
            "status_code": "200",
            "gross_amount": "1250000.00",
            "transaction_status": "settlement",
            "signature_key": "deadbeef_invalid_sig",
        },
    )
    assert r_bad_whk.status_code == 401

    # 4. Call Midtrans webhook with valid SHA512 signature -> 200 PROCESSED
    valid_sig = compute_midtrans_signature(pay_id, "200", "1250000.00")
    r_good_whk = client.post(
        "/api/webhooks/midtrans",
        json={
            "transaction_id": f"evt_ok_{uuid.uuid4().hex[:6]}",
            "order_id": pay_id,
            "status_code": "200",
            "gross_amount": "1250000.00",
            "transaction_status": "settlement",
            "signature_key": valid_sig,
        },
    )
    assert r_good_whk.status_code == 200
    assert r_good_whk.json()["payment_status"] == "PAID"

    # 5. Verify double-entry ledger endpoint reports balanced books
    r_ledger = client.get("/api/bank/ledger")
    assert r_ledger.status_code == 200
    ledger_json = r_ledger.json()
    assert ledger_json["is_balanced"] is True
    assert ledger_json["total_debit_minor"] == ledger_json["total_credit_minor"]

    # 6. Run reconciliation endpoint
    r_recon = client.post("/api/payments/reconcile")
    assert r_recon.status_code == 200
    assert r_recon.json()["status"] == "RECONCILED_CLEAN"
