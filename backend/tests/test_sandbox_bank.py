import pytest
from nacl.signing import SigningKey
from datetime import datetime, timezone, timedelta
from app.schemas.mandate import IntentMandate, CartMandate
from app.bank.service import SandboxBank


@pytest.fixture
def fresh_bank():
    return SandboxBank()


@pytest.fixture
def keys():
    user_key = SigningKey.generate()
    agent_key = SigningKey.generate()
    return user_key, agent_key


def test_sandbox_bank_end_to_end_compliant_flow(fresh_bank, keys):
    user_key, agent_key = keys
    user_pub = user_key.verify_key.encode().hex()
    agent_pub = agent_key.verify_key.encode().hex()

    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=14)

    # 1. User signs Intent Mandate for max 18M IDR
    intent = IntentMandate(
        mandate_id="mandate-test-01",
        user_public_key=user_pub,
        item_query="ThinkPad Laptop",
        max_budget=18000000.0,
        currency="IDR",
        allowed_payment_methods=["DEBIT", "CASH"],
        max_acceptable_apr=0.10,
        allow_cross_border=True,
        cooling_off_seconds=0,
        created_at=now.isoformat(),
        expires_at=expires.isoformat()
    )
    sig_user = user_key.sign(intent.canonical_bytes()).signature
    intent.user_signature = sig_user.hex()

    # 2. Bank registers mandate and reserves sinking pot
    reg_res = fresh_bank.register_intent_mandate(intent)
    assert reg_res["status"] == "REGISTERED"
    assert reg_res["reserved_funds"] == 18000000.0
    assert fresh_bank.accounts["ACC_USER_SINKING_POT"]["balance"] == 18000000.0

    # 3. Agent finds compliant deal for 17.5M IDR and signs Cart Mandate
    cart = CartMandate(
        cart_id="cart-test-01",
        intent_mandate_id=intent.mandate_id,
        merchant_id="LENOVO_AU",
        merchant_name="Lenovo Australia",
        item_title="ThinkPad T14s Gen 4",
        sticker_price=1650.0,
        currency="IDR",
        landed_cost=17500000.0,
        payment_method="DEBIT",
        effective_apr=0.0,
        scam_score=0.05,
        created_at=now.isoformat(),
        agent_public_key=agent_pub
    )
    sig_agent = agent_key.sign(cart.canonical_bytes()).signature
    cart.agent_signature = sig_agent.hex()

    # 4. Bank settles the purchase
    exec_res = fresh_bank.execute_cart_mandate(cart)
    assert exec_res["success"] is True
    assert exec_res["order"]["status"] == "SETTLED_CONFIRMED"
    assert exec_res["disposable_card"]["status"] == "CONSUMED_DESTROYED"
    assert fresh_bank.accounts["ACC_USER_SINKING_POT"]["balance"] == 500000.0  # 18M - 17.5M


def test_bank_blocks_overbudget_cart(fresh_bank, keys):
    user_key, agent_key = keys
    now = datetime.now(timezone.utc)

    intent = IntentMandate(
        mandate_id="mandate-test-02",
        user_public_key=user_key.verify_key.encode().hex(),
        item_query="Laptop",
        max_budget=15000000.0,
        currency="IDR",
        allowed_payment_methods=["DEBIT"],
        created_at=now.isoformat(),
        expires_at=(now + timedelta(days=7)).isoformat()
    )
    intent.user_signature = user_key.sign(intent.canonical_bytes()).signature.hex()
    fresh_bank.register_intent_mandate(intent)

    # Rogue agent attempts to buy laptop for 19M IDR (exceeds 15M cap)
    rogue_cart = CartMandate(
        cart_id="cart-overbudget",
        intent_mandate_id=intent.mandate_id,
        merchant_id="EXPENSIVE_SHOP",
        merchant_name="Luxury Store",
        item_title="Luxury Laptop",
        sticker_price=19000000.0,
        currency="IDR",
        landed_cost=19000000.0,
        payment_method="DEBIT",
        effective_apr=0.0,
        scam_score=0.0,
        created_at=now.isoformat(),
        agent_public_key=agent_key.verify_key.encode().hex()
    )
    rogue_cart.agent_signature = agent_key.sign(rogue_cart.canonical_bytes()).signature.hex()

    exec_res = fresh_bank.execute_cart_mandate(rogue_cart)
    assert exec_res["success"] is False
    assert "BUDGET_EXCEEDED" in exec_res["message"]


def test_bank_blocks_scam_cart_without_override(fresh_bank, keys):
    user_key, agent_key = keys
    now = datetime.now(timezone.utc)

    intent = IntentMandate(
        mandate_id="mandate-test-03",
        user_public_key=user_key.verify_key.encode().hex(),
        item_query="Laptop",
        max_budget=20000000.0,
        currency="IDR",
        allowed_payment_methods=["DEBIT"],
        created_at=now.isoformat(),
        expires_at=(now + timedelta(days=7)).isoformat()
    )
    intent.user_signature = user_key.sign(intent.canonical_bytes()).signature.hex()
    fresh_bank.register_intent_mandate(intent)

    # Cart flagged with 0.85 scam risk (e.g. suspicious domain / extreme low outlier)
    scam_cart = CartMandate(
        cart_id="cart-scam-01",
        intent_mandate_id=intent.mandate_id,
        merchant_id="SCAM_MERCH",
        merchant_name="Unknown Seller",
        item_title="Cheap Laptop",
        sticker_price=4000000.0,
        currency="IDR",
        landed_cost=4000000.0,
        payment_method="DEBIT",
        effective_apr=0.0,
        scam_score=0.85,
        created_at=now.isoformat(),
        agent_public_key=agent_key.verify_key.encode().hex()
    )
    scam_cart.agent_signature = agent_key.sign(scam_cart.canonical_bytes()).signature.hex()

    # Blocked by default
    res_blocked = fresh_bank.execute_cart_mandate(scam_cart)
    assert res_blocked["success"] is False
    assert "SCAM_GATE_TRIGGERED" in res_blocked["message"]

    # Allowed only with explicit user override token from passing Scam Intervention Flow
    res_allowed = fresh_bank.execute_cart_mandate(scam_cart, user_override_token="TOKEN_INTERVENTION_PASSED")
    assert res_allowed["success"] is True
