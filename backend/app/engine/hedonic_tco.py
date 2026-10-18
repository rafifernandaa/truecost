"""
Deterministic Hedonic Ridge Regression Pricer, 36-Month NPV Total Cost of Ownership (TCO),
and 60-Day Cash-Flow Liquidity Projection (per docs/plan.md Tasks 3 & 4).
Zero LLM arithmetic: 100% pure NumPy deterministic calculations.
"""
from typing import Dict, Any, List
import numpy as np


# Pre-calibrated standardized laptop reference matrix (CPU Mark, GPU Mark, RAM GB, SSD GB, Weight kg, Is OLED)
# and corresponding fair market AUD prices for closed-form Ridge Regression (lambda = 1.0)
_REF_FEATURES = np.array([
    [14500, 3200, 8, 256, 1.45, 0],
    [18200, 4500, 16, 512, 1.28, 0],
    [21500, 6200, 16, 512, 1.24, 1],
    [24000, 7800, 16, 1024, 1.35, 1],
    [26500, 8900, 32, 1024, 1.38, 1],
    [31000, 14500, 32, 2048, 1.85, 1],
    [16000, 3800, 16, 256, 1.32, 0],
    [22800, 6800, 16, 512, 1.19, 0],
    [28400, 11200, 32, 1024, 1.55, 1],
    [19500, 5100, 16, 512, 1.30, 0],
], dtype=float)

_REF_PRICES_AUD = np.array([
    980.0,
    1390.0,
    1580.0,
    1790.0,
    2150.0,
    2790.0,
    1150.0,
    1490.0,
    2350.0,
    1420.0,
], dtype=float)


def predict_hedonic_fair_price(
    sticker_price_aud: float,
    cpu_mark: float = 22800.0,
    gpu_mark: float = 6800.0,
    ram_gb: int = 16,
    ssd_gb: int = 512,
    weight_kg: float = 1.24,
    is_oled: bool = False,
    ridge_lambda: float = 1.0,
) -> Dict[str, Any]:
    """
    Fits closed-form Ridge Regression beta = (X^T X + lambda * I)^(-1) X^T y
    on standardized features to predict spec-adjusted fair market value.
    """
    mean_x = _REF_FEATURES.mean(axis=0)
    std_x = _REF_FEATURES.std(axis=0)
    std_x[std_x == 0] = 1.0

    x_norm = (_REF_FEATURES - mean_x) / std_x
    # Add intercept column (unpenalized)
    x_design = np.column_stack([np.ones(len(x_norm)), x_norm])

    penalty = np.eye(x_design.shape[1]) * ridge_lambda
    penalty[0, 0] = 0.0  # Do not penalize intercept

    beta = np.linalg.solve(x_design.T @ x_design + penalty, x_design.T @ _REF_PRICES_AUD)

    query_vec = np.array([cpu_mark, gpu_mark, float(ram_gb), float(ssd_gb), weight_kg, 1.0 if is_oled else 0.0])
    query_norm = (query_vec - mean_x) / std_x
    query_design = np.concatenate([[1.0], query_norm])

    fair_price_aud = float(np.dot(query_design, beta))
    residual_aud = float(sticker_price_aud - fair_price_aud)
    residual_pct = float((residual_aud / fair_price_aud) * 100.0) if fair_price_aud > 0 else 0.0

    return {
        "hedonic_fair_price_aud": round(fair_price_aud, 2),
        "sticker_price_aud": round(float(sticker_price_aud), 2),
        "residual_aud": round(residual_aud, 2),
        "residual_pct": round(residual_pct, 2),
        "is_overpriced": residual_pct > 5.0,
    }


def compute_tco_npv(
    upfront_price_aud: float,
    months: int = 36,
    annual_discount_rate: float = 0.05,
    monthly_energy_cost_aud: float = 2.80,
    resale_value_ratio: float = 0.32,
) -> Dict[str, Any]:
    """
    Computes 36-month Net Present Value (NPV) Total Cost of Ownership:
    NPV = Upfront + sum_{t=1..M} Energy / (1 + r_m)^t - Resale / (1 + r_m)^M
    """
    r_m = (1.0 + annual_discount_rate) ** (1.0 / 12.0) - 1.0
    t_idx = np.arange(1, months + 1, dtype=float)
    discount_factors = (1.0 + r_m) ** t_idx

    pv_energy = float(np.sum(monthly_energy_cost_aud / discount_factors))
    nominal_resale = float(upfront_price_aud * resale_value_ratio)
    pv_resale = float(nominal_resale / ((1.0 + r_m) ** months))

    net_tco_npv = float(upfront_price_aud + pv_energy - pv_resale)

    return {
        "upfront_price_aud": round(float(upfront_price_aud), 2),
        "pv_energy_cost_aud": round(pv_energy, 2),
        "pv_resale_credit_aud": round(pv_resale, 2),
        "net_tco_36m_npv_aud": round(net_tco_npv, 2),
        "effective_monthly_tco_aud": round(net_tco_npv / months, 2),
    }


def project_cashflow_60d(
    current_balance_aud: float,
    purchase_debit_aud: float,
    safety_buffer_aud: float = 500.0,
    daily_burn_aud: float = 18.0,
    biweekly_income_aud: float = 380.0,
) -> Dict[str, Any]:
    """
    Simulates 60-day student liquidity trajectory after purchase_debit_aud
    and flags any breach below safety_buffer_aud.
    """
    balances: List[float] = []
    bal = float(current_balance_aud - purchase_debit_aud)

    for day in range(1, 61):
        bal -= daily_burn_aud
        if day % 14 == 0:
            bal += biweekly_income_aud
        balances.append(round(bal, 2))

    min_balance = float(min(balances)) if balances else bal
    liquidity_breach = min_balance < safety_buffer_aud

    return {
        "starting_balance_aud": round(float(current_balance_aud), 2),
        "post_purchase_day0_aud": round(float(current_balance_aud - purchase_debit_aud), 2),
        "projected_min_balance_60d_aud": round(min_balance, 2),
        "safety_buffer_aud": round(float(safety_buffer_aud), 2),
        "liquidity_breach": bool(liquidity_breach),
        "safe_headroom_aud": round(min_balance - safety_buffer_aud, 2),
    }
