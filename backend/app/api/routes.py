from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.schemas.mandate import IntentMandate, CartMandate
from app.bank.service import bank_service
from app.engine.apr import deconstruct_bnpl_offer
from app.engine.landed_cost import compute_landed_cost
from app.engine.scam_detector import analyze_scam_risk
from app.engine.optimal_stopping import evaluate_buy_timing
from app.engine.topsis import rank_alternatives_topsis

router = APIRouter()

# ----------------- BANK & LEDGER ROUTES -----------------

@router.get("/bank/accounts")
def get_accounts():
    return bank_service.get_account_summary()

@router.get("/bank/transactions")
def get_transactions():
    return {
        "transactions": bank_service.transactions,
        "executed_orders": bank_service.executed_orders,
        "disposable_cards": list(bank_service.disposable_cards.values())
    }

@router.post("/mandates/intent")
def register_intent_mandate(mandate: IntentMandate):
    try:
        res = bank_service.register_intent_mandate(mandate)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/bank/execute-cart")
def execute_cart_mandate(
    cart: CartMandate,
    user_override_token: Optional[str] = Body(None, embed=True)
):
    res = bank_service.execute_cart_mandate(cart, user_override_token)
    if not res.get("success"):
        raise HTTPException(status_code=403, detail=res)
    return res

# ----------------- DETERMINISTIC QUANT ROUTES -----------------

class BNPLRequest(BaseModel):
    sticker_price: float
    tenor_months: int
    monthly_installment: float
    upfront_admin_fee: float = 0.0
    monthly_service_fee: float = 0.0
    cash_discount_amount: float = 0.0

@router.post("/quant/deconstruct-bnpl")
def api_deconstruct_bnpl(req: BNPLRequest):
    return deconstruct_bnpl_offer(
        sticker_price=req.sticker_price,
        tenor_months=req.tenor_months,
        monthly_installment=req.monthly_installment,
        upfront_admin_fee=req.upfront_admin_fee,
        monthly_service_fee=req.monthly_service_fee,
        cash_discount_amount=req.cash_discount_amount
    )

class LandedCostRequest(BaseModel):
    item_price_foreign: float
    foreign_currency: str
    target_currency: str = "IDR"
    fx_spot_rate: float = 10400.0
    fx_spread_percent: float = 0.025
    shipping_and_insurance_foreign: float = 0.0
    has_npwp: bool = True
    is_tourist_refund_eligible: bool = False

@router.post("/quant/landed-cost")
def api_landed_cost(req: LandedCostRequest):
    return compute_landed_cost(
        item_price_foreign=req.item_price_foreign,
        foreign_currency=req.foreign_currency,
        target_currency=req.target_currency,
        fx_spot_rate=req.fx_spot_rate,
        fx_spread_percent=req.fx_spread_percent,
        shipping_and_insurance_foreign=req.shipping_and_insurance_foreign,
        has_npwp=req.has_npwp,
        is_tourist_refund_eligible=req.is_tourist_refund_eligible
    )

class ScamCheckRequest(BaseModel):
    listing_price: float
    market_prices: List[float]
    seller_feedback_score: Optional[float] = 98.0
    seller_review_count: Optional[int] = 150
    seller_account_age_days: Optional[int] = 365
    listing_url: Optional[str] = None
    demands_off_platform_payment: bool = False

@router.post("/quant/scam-check")
def api_scam_check(req: ScamCheckRequest):
    return analyze_scam_risk(
        listing_price=req.listing_price,
        market_prices=req.market_prices,
        seller_feedback_score=req.seller_feedback_score,
        seller_review_count=req.seller_review_count,
        seller_account_age_days=req.seller_account_age_days,
        listing_url=req.listing_url,
        demands_off_platform_payment=req.demands_off_platform_payment
    )

class BuyTimingRequest(BaseModel):
    current_price: float
    price_history: List[float]
    days_elapsed: int
    total_deadline_days: int

@router.post("/quant/buy-timing")
def api_buy_timing(req: BuyTimingRequest):
    return evaluate_buy_timing(
        current_price=req.current_price,
        price_history=req.price_history,
        days_elapsed=req.days_elapsed,
        total_deadline_days=req.total_deadline_days
    )

class TopsisRequest(BaseModel):
    candidates: List[Dict[str, Any]]
    criteria_weights: Dict[str, float]
    criteria_types: Dict[str, str]

@router.post("/quant/topsis-rank")
def api_topsis_rank(req: TopsisRequest):
    return rank_alternatives_topsis(
        candidates=req.candidates,
        criteria_weights=req.criteria_weights,
        criteria_types=req.criteria_types
    )
