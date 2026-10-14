import pytest
from app.engine.apr import deconstruct_bnpl_offer, calculate_irr_cashflows


def test_true_zero_percent_installment():
    # 12,000,000 IDR over 6 months with 2,000,000 IDR per month, no fees
    result = deconstruct_bnpl_offer(
        sticker_price=12000000.0,
        tenor_months=6,
        monthly_installment=2000000.0,
        upfront_admin_fee=0.0,
        monthly_service_fee=0.0,
        cash_discount_amount=0.0
    )
    assert result["total_finance_charge"] == 0.0
    assert result["nominal_apr"] == 0.0
    assert result["effective_annual_rate"] == 0.0
    assert not result["is_predatory"]


def test_advertised_zero_percent_with_hidden_fees():
    # 12,000,000 IDR over 6 months:
    # 2,000,000 / mo + 50,000 upfront admin + 25,000 / mo service fee
    result = deconstruct_bnpl_offer(
        sticker_price=12000000.0,
        tenor_months=6,
        monthly_installment=2000000.0,
        upfront_admin_fee=50000.0,
        monthly_service_fee=25000.0,
        cash_discount_amount=0.0
    )
    assert result["total_finance_charge"] == 200000.0
    assert result["nominal_apr"] > 0.04  # ~5.7% APR
    assert result["effective_annual_rate"] > 0.04
    assert not result["is_predatory"]


def test_predatory_bnpl_with_foregone_cash_discount():
    # Item is 10,000,000 IDR. If paid cash, seller offers 10% discount (9,000,000).
    # BNPL charges 10,000,000 over 3 months (3,333,333 / mo) plus 200,000 admin fee.
    result = deconstruct_bnpl_offer(
        sticker_price=10000000.0,
        tenor_months=3,
        monthly_installment=3333333.33,
        upfront_admin_fee=200000.0,
        monthly_service_fee=0.0,
        cash_discount_amount=1000000.0
    )
    # Foregoing 1M discount + 200k admin = ~1.2M finance charge on 9M borrowed for 3 months
    assert result["total_finance_charge"] == pytest.approx(1200000.0, rel=1e-4)
    assert result["effective_annual_rate"] > 0.40  # Massive >40% APR!
    assert result["is_predatory"]

