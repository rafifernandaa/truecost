from app.engine.hedonic_tco import (
    predict_hedonic_fair_price,
    compute_tco_npv,
    project_cashflow_60d,
)


def test_hedonic_monotonic_spec_scaling():
    base_16gb = predict_hedonic_fair_price(
        sticker_price_aud=1580.0,
        cpu_mark=21500.0,
        gpu_mark=6200.0,
        ram_gb=16,
        ssd_gb=512,
    )
    high_32gb = predict_hedonic_fair_price(
        sticker_price_aud=2200.0,
        cpu_mark=26500.0,
        gpu_mark=8900.0,
        ram_gb=32,
        ssd_gb=1024,
        is_oled=True,
    )
    assert high_32gb["hedonic_fair_price_aud"] > base_16gb["hedonic_fair_price_aud"]


def test_compute_tco_npv_resale_reduces_net_cost():
    res = compute_tco_npv(
        upfront_price_aud=1580.0,
        months=36,
        annual_discount_rate=0.05,
        monthly_energy_cost_aud=2.50,
        resale_value_ratio=0.35,
    )
    assert res["pv_resale_credit_aud"] > 0
    assert res["net_tco_36m_npv_aud"] < res["upfront_price_aud"]


def test_project_cashflow_60d_breach_detection():
    safe_res = project_cashflow_60d(
        current_balance_aud=2450.0,
        purchase_debit_aud=1490.0,
        safety_buffer_aud=500.0,
    )
    assert safe_res["liquidity_breach"] is False

    breach_res = project_cashflow_60d(
        current_balance_aud=2450.0,
        purchase_debit_aud=2100.0,
        safety_buffer_aud=500.0,
    )
    assert breach_res["liquidity_breach"] is True
