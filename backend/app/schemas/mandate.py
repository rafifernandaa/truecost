from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import base64
from nacl.signing import SigningKey, VerifyKey
from nacl.exceptions import BadSignatureError


class IntentMandate(BaseModel):
    """
    User-signed mandate bounding the AI agent's purchasing authority.
    Modelled after Google AP2 (Agent Payments Protocol) Intent Mandate.
    """
    mandate_id: str
    user_public_key: str  # Hex-encoded Ed25519 public key
    item_query: str
    max_budget: float
    currency: str = "IDR"
    allowed_payment_methods: List[str] = Field(default_factory=lambda: ["CASH", "DEBIT", "BNPL_VERIFIED"])
    max_acceptable_apr: float = 0.20  # Max 20% effective APR
    allow_cross_border: bool = True
    cooling_off_seconds: int = 0
    created_at: str
    expires_at: str
    user_signature: Optional[str] = None  # Hex-encoded Ed25519 signature

    def canonical_bytes(self) -> bytes:
        """Produce deterministic canonical JSON bytes for cryptographic signing."""
        data = {
            "mandate_id": self.mandate_id,
            "user_public_key": self.user_public_key,
            "item_query": self.item_query,
            "max_budget": float(self.max_budget),
            "currency": self.currency,
            "allowed_payment_methods": sorted(self.allowed_payment_methods),
            "max_acceptable_apr": float(self.max_acceptable_apr),
            "allow_cross_border": self.allow_cross_border,
            "cooling_off_seconds": self.cooling_off_seconds,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
        }
        return json.dumps(data, sort_keys=True, separators=(',', ':')).encode('utf-8')

    def verify_signature(self) -> bool:
        if not self.user_signature:
            return False
        try:
            pubkey_bytes = bytes.fromhex(self.user_public_key)
            sig_bytes = bytes.fromhex(self.user_signature)
            verify_key = VerifyKey(pubkey_bytes)
            verify_key.verify(self.canonical_bytes(), sig_bytes)
            return True
        except (ValueError, BadSignatureError):
            return False


class CartMandate(BaseModel):
    """
    Agent-generated and signed cart lock referencing the parent Intent Mandate.
    """
    cart_id: str
    intent_mandate_id: str
    merchant_id: str
    merchant_name: str
    item_title: str
    sticker_price: float
    currency: str
    landed_cost: float
    payment_method: str
    effective_apr: float
    scam_score: float
    created_at: str
    agent_public_key: str
    agent_signature: Optional[str] = None

    def canonical_bytes(self) -> bytes:
        data = {
            "cart_id": self.cart_id,
            "intent_mandate_id": self.intent_mandate_id,
            "merchant_id": self.merchant_id,
            "merchant_name": self.merchant_name,
            "item_title": self.item_title,
            "sticker_price": float(self.sticker_price),
            "currency": self.currency,
            "landed_cost": float(self.landed_cost),
            "payment_method": self.payment_method,
            "effective_apr": float(self.effective_apr),
            "scam_score": float(self.scam_score),
            "created_at": self.created_at,
            "agent_public_key": self.agent_public_key,
        }
        return json.dumps(data, sort_keys=True, separators=(',', ':')).encode('utf-8')

    def verify_signature(self) -> bool:
        if not self.agent_signature:
            return False
        try:
            pubkey_bytes = bytes.fromhex(self.agent_public_key)
            sig_bytes = bytes.fromhex(self.agent_signature)
            verify_key = VerifyKey(pubkey_bytes)
            verify_key.verify(self.canonical_bytes(), sig_bytes)
            return True
        except (ValueError, BadSignatureError):
            return False
