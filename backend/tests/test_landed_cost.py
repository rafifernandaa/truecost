import pytest
from app.engine.landed_cost import compute_landed_cost


def test_australian_laptop_purchase_with_tourist_refund():
    # Laptop costs 1,500 AUD
    # Spot FX: 1 AUD = 10,400 IDR
    # 2.5% card FX spread
    # Tourist Refund (TRS): 10% refund on 1500 AUD = 150 AUD
    # Personal passenger with USD 500 (~769 AUD) duty-free allowance
    res = compute_landed_cost(
        item_price_foreign=1500.0,
        foreign_currency="AUD",
        target_currency="IDR",
        fx_spot_rate=10400.0,
        fx_spread_percent=0.025,
        shipping_and_insurance_foreign=0.0,
        has_npwp=True,
        is_tourist_refund_eligible=True,
        tourist_tax_rate=0.10,
        is_personal_passenger=True,
        passenger_de_minimis_usd=500.0,
        usd_to_foreign_rate=0.65
    )

    assert res["effective_fx_rate"] == pytest.approx(10660.0)
    assert res["tourist_tax_refund"] > 1500000.0  # 150 AUD * 10,660 = ~1,599,000 IDR

    assert res["import_tax_breakdown"]["total_customs_taxes"] > 0
    # Final landed cost should reflect: base + taxes - refund
    assert res["final_landed_cost"] > 0
    assert res["target_currency"] == "IDR"
