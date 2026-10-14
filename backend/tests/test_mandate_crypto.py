import pytest
from nacl.signing import SigningKey
from datetime import datetime, timezone, timedelta
from app.schemas.mandate import IntentMandate, CartMandate


def test_intent_mandate_signing_and_tamper_detection():
    # 1. Generate user Ed25519 keypair
    user_signing_key = SigningKey.generate()
    user_pubkey_hex = user_signing_key.verify_key.encode().hex()

    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=14)

    mandate = IntentMandate(
        mandate_id="mandate-101",
        user_public_key=user_pubkey_hex,
        item_query="Lenovo ThinkPad X1 Carbon 16GB",
        max_budget=18000000.0,
        currency="IDR",
        allowed_payment_methods=["CASH", "DEBIT", "BNPL_VERIFIED"],
        max_acceptable_apr=0.15,
        allow_cross_border=True,
        cooling_off_seconds=0,
        created_at=now.isoformat(),
        expires_at=expires.isoformat()
    )

    # 2. Sign canonical bytes
    sig = user_signing_key.sign(mandate.canonical_bytes()).signature
    mandate.user_signature = sig.hex()

    # 3. Signature verification succeeds
    assert mandate.verify_signature() is True

    # 4. Tamper attempt: Mallory modifies max_budget to 50M IDR
    mandate.max_budget = 50000000.0
    assert mandate.verify_signature() is False


def test_cart_mandate_signing_and_verification():
    agent_signing_key = SigningKey.generate()
    agent_pubkey_hex = agent_signing_key.verify_key.encode().hex()

    cart = CartMandate(
        cart_id="cart-501",
        intent_mandate_id="mandate-101",
        merchant_id="MERCH_LENOVO_AU",
        merchant_name="Lenovo Official AU Store",
        item_title="ThinkPad X1 Carbon Gen 11",
        sticker_price=1650.0,
        currency="AUD",
        landed_cost=17400000.0,
        payment_method="DEBIT",
        effective_apr=0.0,
        scam_score=0.05,
        created_at=datetime.now(timezone.utc).isoformat(),
        agent_public_key=agent_pubkey_hex
    )

    sig = agent_signing_key.sign(cart.canonical_bytes()).signature
    cart.agent_signature = sig.hex()

    assert cart.verify_signature() is True

    # Tampering test
    cart.landed_cost = 25000000.0
    assert cart.verify_signature() is False
