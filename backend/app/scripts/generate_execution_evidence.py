import json
import os
from datetime import datetime, timezone, timedelta
from nacl.signing import SigningKey

from app.schemas.mandate import IntentMandate, CartMandate
from app.bank.service import SandboxBank
from app.engine.apr import deconstruct_bnpl_offer
from app.engine.landed_cost import compute_landed_cost
from app.engine.scam_detector import analyze_scam_risk
from app.engine.optimal_stopping import evaluate_buy_timing


def generate_full_audit_evidence():
    bank = SandboxBank()
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    evidence_file = os.path.join(logs_dir, "sandbox_execution.jsonl")

    # Cryptographic Identities
    user_key = SigningKey.generate()
    agent_key = SigningKey.generate()

    user_pub = user_key.verify_key.encode().hex()
    agent_pub = agent_key.verify_key.encode().hex()

    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=14)

    # ---------------- SCENARIO 1: Intent Mandate Registration ----------------
    intent = IntentMandate(
        mandate_id="MANDATE-2026-FINTECH-001",
        user_public_key=user_pub,
        item_query="Lenovo ThinkPad T14s Gen 4 (16GB RAM, 512GB SSD)",
        max_budget=18500000.0,
        currency="IDR",
        allowed_payment_methods=["DEBIT", "CASH"],
        max_acceptable_apr=0.15,
        allow_cross_border=True,
        cooling_off_seconds=0,
        created_at=now.isoformat(),
        expires_at=expires.isoformat()
    )
    intent.user_signature = user_key.sign(intent.canonical_bytes()).signature.hex()

    reg_res = bank.register_intent_mandate(intent)

    # ---------------- SCENARIO 2: Market Watching & Timing Evaluation ----------------
    price_history = [16200000.0, 16800000.0, 17200000.0, 17500000.0, 18200000.0, 18900000.0]
    timing_eval = evaluate_buy_timing(
        current_price=16400000.0,
        price_history=price_history,
        days_elapsed=4,
        total_deadline_days=14
    )

    # ---------------- SCENARIO 3: Cross-Border Landed Cost Calculation ----------------
    landed_eval = compute_landed_cost(
        item_price_foreign=1580.0,
        foreign_currency="AUD",
        target_currency="IDR",
        fx_spot_rate=10400.0,
        fx_spread_percent=0.025,
        has_npwp=True,
        is_tourist_refund_eligible=True,
        tourist_tax_rate=0.10,
        is_personal_passenger=True,
        passenger_de_minimis_usd=500.0
    )

    # ---------------- SCENARIO 4: Scam Anomaly Analysis ----------------
    scam_eval = analyze_scam_risk(
        listing_price=16400000.0,
        market_prices=price_history,
        seller_feedback_score=98.5,
        seller_review_count=340,
        seller_account_age_days=520,
        listing_url="https://www.ebay.com.au/itm/lenovo-thinkpad-t14s-gen4"
    )

    # ---------------- SCENARIO 5: Cart Mandate Assembly & Bank Execution ----------------
    cart = CartMandate(
        cart_id="CART-2026-EXEC-099",
        intent_mandate_id=intent.mandate_id,
        merchant_id="LENOVO_OFFICIAL_AU",
        merchant_name="Lenovo Official Store Australia",
        item_title="Lenovo ThinkPad T14s Gen 4 (16GB RAM, 512GB SSD)",
        sticker_price=1580.0,
        currency="IDR",
        landed_cost=landed_eval["final_landed_cost"],
        payment_method="DEBIT",
        effective_apr=0.0,
        scam_score=scam_eval["scam_score"],
        created_at=(now + timedelta(days=4)).isoformat(),
        agent_public_key=agent_pub
    )
    cart.agent_signature = agent_key.sign(cart.canonical_bytes()).signature.hex()

    exec_res = bank.execute_cart_mandate(cart)

    # ---------------- SCENARIO 6: Rogue Attacker Rejection ----------------
    malicious_cart = CartMandate(
        cart_id="CART-ROGUE-ATTACK",
        intent_mandate_id=intent.mandate_id,
        merchant_id="UNKNOWN_ATTACKER",
        merchant_name="Fake Electronics Store",
        item_title="Overpriced Laptop",
        sticker_price=25000000.0,
        currency="IDR",
        landed_cost=25000000.0,
        payment_method="DEBIT",
        effective_apr=0.0,
        scam_score=0.1,
        created_at=(now + timedelta(days=5)).isoformat(),
        agent_public_key=agent_pub
    )
    malicious_cart.agent_signature = agent_key.sign(malicious_cart.canonical_bytes()).signature.hex()
    rejected_res = bank.execute_cart_mandate(malicious_cart)

    # Write unified JSONL execution trajectory
    trajectory_records = [
        {"event": "INTENT_MANDATE_REGISTERED", "payload": intent.model_dump(), "bank_result": reg_res},
        {"event": "TIMING_DECISION_OPTIMAL_STOPPING", "payload": timing_eval},
        {"event": "CROSS_BORDER_LANDED_COST_EVALUATION", "payload": landed_eval},
        {"event": "SCAM_OUTLIER_RISK_CHECK", "payload": scam_eval},
        {"event": "CART_MANDATE_COMPLIANT_SETTLEMENT", "payload": cart.model_dump(), "bank_result": exec_res},
        {"event": "BANK_BLOCKED_POLICY_VIOLATION", "payload": malicious_cart.model_dump(), "bank_result": rejected_res}
    ]

    with open(evidence_file, "w", encoding="utf-8") as f:
        for rec in trajectory_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"Successfully generated execution evidence log at: {evidence_file}")
    return trajectory_records


if __name__ == "__main__":
    generate_full_audit_evidence()
