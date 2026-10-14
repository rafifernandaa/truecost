import numpy as np
from typing import List, Dict, Any, Optional
import scipy.optimize as opt


def calculate_irr_cashflows(cash_flows: List[float], max_iter: int = 1000) -> Optional[float]:
    """
    Calculate the monthly Internal Rate of Return (IRR) for a series of cash flows.
    cash_flows[0]: net cash received/value obtained (positive)
    cash_flows[1:]: net cash paid out in each subsequent period (negative)
    """
    if len(cash_flows) < 2:
        return 0.0

    # If all outflow equals inflow with no fees, IRR is 0.0
    if abs(sum(cash_flows)) < 1e-6:
        return 0.0

    def npv(rate: float) -> float:
        val = 0.0
        for t, cf in enumerate(cash_flows):
            val += cf / ((1.0 + rate) ** t)
        return val

    try:
        # Solve for rate where NPV = 0
        res = opt.root_scalar(npv, bracket=[-0.5, 5.0], method='brentq')
        if res.converged:
            return float(res.root)
    except Exception:
        pass

    try:
        # Fallback to newton
        res = opt.newton(npv, x0=0.05, maxiter=max_iter)
        return float(res)
    except Exception:
        return None


def deconstruct_bnpl_offer(
    sticker_price: float,
    tenor_months: int,
    monthly_installment: float,
    upfront_admin_fee: float = 0.0,
    monthly_service_fee: float = 0.0,
    cash_discount_amount: float = 0.0
) -> Dict[str, Any]:
    """
    Deconstructs an advertised installment / BNPL plan to uncover hidden fees and true APR.
    
    Parameters:
    - sticker_price: The nominal price of the product
    - tenor_months: Number of monthly repayment cycles
    - monthly_installment: The nominal installment billed per month
    - upfront_admin_fee: One-off fee charged at checkout
    - monthly_service_fee: Hidden recurring platform/service fee
    - cash_discount_amount: Opportunity cost if cash/direct payment receives an immediate discount
    
    Returns:
    - total_amount_paid: Total cash disbursed
    - total_finance_charge: Excess paid over the best direct price
    - monthly_effective_rate: Periodic IRR
    - nominal_apr: Monthly rate * 12
    - effective_annual_rate (EAR): (1 + monthly_rate)^12 - 1
    - is_predatory: True if EAR exceeds regulatory or reasonable thresholds (e.g. > 36%)
    """
    # Net economic value received at t=0
    # If paying cash would cost (sticker_price - cash_discount_amount),
    # then choosing the installment effectively borrows only that discounted base.
    base_cash_value = sticker_price - cash_discount_amount
    net_cf_0 = base_cash_value - upfront_admin_fee

    effective_monthly_payment = monthly_installment + monthly_service_fee
    cash_flows = [net_cf_0] + [-effective_monthly_payment] * tenor_months

    total_amount_paid = upfront_admin_fee + (effective_monthly_payment * tenor_months)
    total_finance_charge = total_amount_paid - base_cash_value

    monthly_rate = calculate_irr_cashflows(cash_flows)

    if monthly_rate is None or monthly_rate < 0:
        nominal_apr = 0.0
        ear = 0.0
    else:
        nominal_apr = monthly_rate * 12.0
        ear = ((1.0 + monthly_rate) ** 12.0) - 1.0

    return {
        "sticker_price": round(sticker_price, 2),
        "tenor_months": tenor_months,
        "base_cash_value": round(base_cash_value, 2),
        "total_amount_paid": round(total_amount_paid, 2),
        "total_finance_charge": round(total_finance_charge, 2),
        "monthly_effective_rate": round(monthly_rate if monthly_rate else 0.0, 4),
        "nominal_apr": round(nominal_apr, 4),
        "effective_annual_rate": round(ear, 4),
        "is_predatory": ear > 0.36 or total_finance_charge > (0.20 * sticker_price),
        "analysis_summary": (
            f"Advertised as 0%, but true Effective Annual Rate (EAR) is {round(ear * 100, 2)}% "
            f"with total financing charges of {round(total_finance_charge, 2)}."
            if total_finance_charge > 1.0 else "True 0% interest with zero hidden financing charges."
        )
    }
