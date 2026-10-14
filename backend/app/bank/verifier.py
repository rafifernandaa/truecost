from typing import Tuple, Dict, Any, Optional
from datetime import datetime
from app.schemas.mandate import IntentMandate, CartMandate


class MandatePolicyViolation(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


def verify_cart_against_intent(
    intent: IntentMandate,
    cart: CartMandate,
    user_override_token: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Independent banking policy verification before moving funds.
    Enforces that the AI agent strictly operated within user cryptographic constraints.
    """
    # 1. Verify User Cryptographic Signature on Intent Mandate
    if not intent.verify_signature():
        return False, "INVALID_USER_SIGNATURE: Intent mandate signature check failed."

    # 2. Verify Agent Cryptographic Signature on Cart Mandate
    if not cart.verify_signature():
        return False, "INVALID_AGENT_SIGNATURE: Cart mandate signature check failed."

    # 3. Mandate Association Check
    if cart.intent_mandate_id != intent.mandate_id:
        return False, f"MISMATCHED_MANDATE: Cart references {cart.intent_mandate_id}, expected {intent.mandate_id}."

    # 4. Expiration Check
    try:
        expires_at = datetime.fromisoformat(intent.expires_at)
        cart_created = datetime.fromisoformat(cart.created_at)
        if cart_created > expires_at:
            return False, f"MANDATE_EXPIRED: Intent mandate expired at {intent.expires_at}."
    except Exception as e:
        return False, f"MALFORMED_TIMESTAMP: {str(e)}"

    # 5. Budget Cap Check (Hard Boundary)
    if cart.landed_cost > intent.max_budget:
        return False, (
            f"BUDGET_EXCEEDED: Cart landed cost ({cart.landed_cost:,.2f} {cart.currency}) "
            f"exceeds user authorized cap ({intent.max_budget:,.2f} {intent.currency})."
        )

    # 6. Payment Method & APR Policy
    if cart.payment_method not in intent.allowed_payment_methods:
        return False, (
            f"DISALLOWED_PAYMENT_METHOD: {cart.payment_method} is not in user permitted methods "
            f"({intent.allowed_payment_methods})."
        )

    if cart.effective_apr > intent.max_acceptable_apr:
        return False, (
            f"APR_EXCEEDED: Effective APR ({cart.effective_apr * 100:.2f}%) exceeds "
            f"user cap ({intent.max_acceptable_apr * 100:.2f}%)."
        )

    # 7. Scam Protection Gate (Revolut-style Anomaly Block)
    if cart.scam_score >= 0.50 and not user_override_token:
        return False, (
            f"SCAM_GATE_TRIGGERED: Scam risk score {cart.scam_score:.2f} requires "
            f"explicit user Scam Intervention Flow verification override."
        )

    return True, "VERIFICATION_SUCCESS: Cart conforms strictly to user signed intent."
