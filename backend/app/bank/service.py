import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.schemas.mandate import IntentMandate, CartMandate
from app.bank.verifier import verify_cart_against_intent


class SandboxBank:
    """
    Simulated Core Banking Service with atomic double-entry ledger,
    sinking pots, single-use disposable cards, and cryptographically verified debits.
    """
    def __init__(self):
        # Default user account state
        self.accounts: Dict[str, Dict[str, Any]] = {
            "ACC_USER_CHECKING": {
                "account_id": "ACC_USER_CHECKING",
                "name": "Primary Student Checking Account",
                "currency": "IDR",
                "balance": 25000000.0,  # 25 Million IDR (~1,600 USD)
                "status": "ACTIVE"
            },
            "ACC_USER_SINKING_POT": {
                "account_id": "ACC_USER_SINKING_POT",
                "name": "Laptop Purchase Sinking Fund Pot",
                "currency": "IDR",
                "balance": 0.0,
                "status": "ACTIVE"
            }
        }
        self.intent_mandates: Dict[str, IntentMandate] = {}
        self.disposable_cards: Dict[str, Dict[str, Any]] = {}
        self.transactions: List[Dict[str, Any]] = []
        self.executed_orders: List[Dict[str, Any]] = []

    def get_account_summary(self) -> Dict[str, Any]:
        return {
            "accounts": list(self.accounts.values()),
            "total_liquid_idr": sum(acc["balance"] for acc in self.accounts.values()),
            "active_intent_mandates": len(self.intent_mandates),
            "executed_orders_count": len(self.executed_orders),
            "disposable_cards_count": len(self.disposable_cards)
        }

    def register_intent_mandate(self, mandate: IntentMandate) -> Dict[str, Any]:
        """
        Registers a user's signed Intent Mandate and optionally reserves funds in a sinking pot.
        """
        if not mandate.verify_signature():
            raise ValueError("Cannot register mandate: Invalid cryptographic signature.")

        self.intent_mandates[mandate.mandate_id] = mandate

        # Lock budget into the sinking pot (Tier 1 autonomous reservation)
        checking = self.accounts["ACC_USER_CHECKING"]
        pot = self.accounts["ACC_USER_SINKING_POT"]

        reserve_amount = min(checking["balance"], mandate.max_budget)
        checking["balance"] -= reserve_amount
        pot["balance"] += reserve_amount

        tx = {
            "tx_id": str(uuid.uuid4()),
            "type": "RESERVE_SINKING_POT",
            "amount": reserve_amount,
            "currency": mandate.currency,
            "from_account": checking["account_id"],
            "to_account": pot["account_id"],
            "mandate_id": mandate.mandate_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "COMPLETED"
        }
        self.transactions.append(tx)

        return {
            "status": "REGISTERED",
            "mandate_id": mandate.mandate_id,
            "reserved_funds": reserve_amount,
            "pot_balance": pot["balance"],
            "checking_balance": checking["balance"]
        }

    def generate_disposable_card(self, cart: CartMandate) -> Dict[str, Any]:
        """
        Generates a Revolut-style single-use virtual card token locked to the exact cart amount and merchant.
        """
        card_id = f"VCARD_{uuid.uuid4().hex[:12].upper()}"
        card = {
            "card_id": card_id,
            "cart_id": cart.cart_id,
            "masked_pan": f"4532-XXXX-XXXX-{uuid.uuid4().hex[:4].upper()}",
            "currency": cart.currency,
            "spending_limit": cart.landed_cost,
            "merchant_id": cart.merchant_id,
            "status": "ACTIVE_SINGLE_USE",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        self.disposable_cards[card_id] = card
        return card

    def execute_cart_mandate(
        self,
        cart: CartMandate,
        user_override_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Performs the independent verification and executes the debit.
        """
        intent = self.intent_mandates.get(cart.intent_mandate_id)
        if not intent:
            return {
                "success": False,
                "error_code": "MANDATE_NOT_FOUND",
                "message": f"Parent Intent Mandate {cart.intent_mandate_id} is not registered."
            }

        # 1. Independent policy verification
        valid, reason = verify_cart_against_intent(intent, cart, user_override_token)
        if not valid:
            # Log rejected attempt for audit trail
            rejection_log = {
                "tx_id": str(uuid.uuid4()),
                "type": "PURCHASE_REJECTED",
                "cart_id": cart.cart_id,
                "intent_mandate_id": intent.mandate_id,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "REJECTED_BY_BANK_POLICY"
            }
            self.transactions.append(rejection_log)
            return {
                "success": False,
                "error_code": "BANK_POLICY_VIOLATION",
                "message": reason,
                "rejection_log": rejection_log
            }

        # 2. Check sufficient funds in sinking pot or checking
        pot = self.accounts["ACC_USER_SINKING_POT"]
        checking = self.accounts["ACC_USER_CHECKING"]

        debit_amount = cart.landed_cost
        if pot["balance"] >= debit_amount:
            pot["balance"] -= debit_amount
            debit_from = pot["account_id"]
        elif (pot["balance"] + checking["balance"]) >= debit_amount:
            from_pot = pot["balance"]
            from_checking = debit_amount - from_pot
            pot["balance"] = 0.0
            checking["balance"] -= from_checking
            debit_from = "COMBINED_POT_AND_CHECKING"
        else:
            return {
                "success": False,
                "error_code": "INSUFFICIENT_FUNDS",
                "message": f"Insufficient balance to debit {debit_amount:,.2f} {cart.currency}."
            }

        # 3. Issue single-use disposable card token
        disposable_card = self.generate_disposable_card(cart)
        disposable_card["status"] = "CONSUMED_DESTROYED"

        # 4. Atomic settlement record
        order_record = {
            "order_id": f"ORD_{uuid.uuid4().hex[:8].upper()}",
            "cart_id": cart.cart_id,
            "intent_mandate_id": intent.mandate_id,
            "item_title": cart.item_title,
            "merchant_name": cart.merchant_name,
            "sticker_price": cart.sticker_price,
            "final_landed_cost": cart.landed_cost,
            "currency": cart.currency,
            "payment_method": cart.payment_method,
            "effective_apr": cart.effective_apr,
            "disposable_card_id": disposable_card["card_id"],
            "debit_source": debit_from,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "SETTLED_CONFIRMED"
        }
        self.executed_orders.append(order_record)

        tx_log = {
            "tx_id": str(uuid.uuid4()),
            "type": "PURCHASE_SETTLEMENT",
            "order_id": order_record["order_id"],
            "amount": debit_amount,
            "currency": cart.currency,
            "from_account": debit_from,
            "to_merchant": cart.merchant_name,
            "timestamp": order_record["timestamp"],
            "status": "COMPLETED"
        }
        self.transactions.append(tx_log)

        return {
            "success": True,
            "order": order_record,
            "transaction": tx_log,
            "remaining_checking_balance": checking["balance"],
            "remaining_pot_balance": pot["balance"],
            "disposable_card": disposable_card
        }


# Singleton instance for the demo service
bank_service = SandboxBank()
