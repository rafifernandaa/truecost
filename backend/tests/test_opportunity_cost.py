"""
Tests for Deterministic Opportunity Cost & Human Capital Quant Engine.
Validates compounding precision, zero floating-point drift, life energy calculations,
and role-based upskilling catalogs.
"""
import pytest
from app.engine.opportunity_cost import (
    compute_compound_opportunity_cost,
    get_human_capital_alternatives,
    calculate_life_energy_hours,
)


def test_compute_compound_opportunity_cost_precision():
    principal = 10_000_000.0  # Rp 10M
    rate = 0.06  # 6% annual
    res = compute_compound_opportunity_cost(principal=principal, annual_rate=rate, compounding_frequency=12)

    assert res["principal"] == 10_000_000.0
    assert res["annual_rate"] == 0.06
    assert res["rule_of_72_doubling_years"] == 12.0

    projections = res["projections"]
    assert len(projections) == 5  # 1, 3, 5, 10, 20 years

    p1 = next(p for p in projections if p["horizon_years"] == 1)
    p5 = next(p for p in projections if p["horizon_years"] == 5)
    p10 = next(p for p in projections if p["horizon_years"] == 10)

    # Hand verification for 1y monthly compounding: 10M * (1 + 0.06/12)^12 = 10,616,778.12
    expected_1y = round(10_000_000.0 * ((1.0 + 0.06 / 12) ** 12), 2)
    assert p1["future_value"] == expected_1y
    assert p1["interest_earned"] == round(expected_1y - 10_000_000.0, 2)
    assert p1["multiple"] > 1.05

    # 5y should be greater than 1y, 10y should be greater than 5y
    assert p5["future_value"] > p1["future_value"]
    assert p10["future_value"] > p5["future_value"]
    assert p5["future_value_aggressive"] > p5["future_value"] > p5["future_value_conservative"]


def test_compute_compound_opportunity_cost_edge_cases():
    # Zero principal
    res_zero = compute_compound_opportunity_cost(principal=0.0)
    assert res_zero["principal"] == 0.0
    assert res_zero["default_5y_future_value"] == 0.0

    # Negative principal handled safely as 0
    res_neg = compute_compound_opportunity_cost(principal=-5000.0)
    assert res_neg["principal"] == 0.0


def test_get_human_capital_alternatives_tech_software():
    # Rp 16,000,000 budget (~$1,000 USD)
    res = get_human_capital_alternatives(
        budget_amount=16_000_000.0,
        currency="IDR",
        role="tech_software",
        usd_to_idr=16_000.0,
    )

    assert res["role"] == "tech_software"
    assert res["currency"] == "IDR"
    assert res["budget_input"] == 16_000_000.0
    assert len(res["recommended_bundle"]) >= 2

    # AWS Cert ($150) and O'Reilly ($399) should easily fit within $1,000 USD
    bundle_names = [it["name"] for it in res["recommended_bundle"]]
    assert any("AWS" in n for n in bundle_names)
    assert any("O'Reilly" in n for n in bundle_names)
    assert res["total_bundle_cost"] <= 16_000_000.0 * 1.05
    assert res["surplus_remaining"] >= 0.0


def test_get_human_capital_alternatives_small_budget_fractional():
    # Only Rp 500,000 (~$31.25 USD)
    res = get_human_capital_alternatives(
        budget_amount=500_000.0,
        currency="IDR",
        role="design_creative",
        usd_to_idr=16_000.0,
    )

    assert res["role"] == "design_creative"
    assert len(res["recommended_bundle"]) == 1
    item = res["recommended_bundle"][0]
    assert item.get("is_fractional") is True
    assert 0.0 < item.get("pct_funded", 0.0) < 100.0


def test_get_human_capital_alternatives_all_roles():
    roles = ["tech_software", "design_creative", "business_finance", "student_academic"]
    for role in roles:
        res = get_human_capital_alternatives(
            budget_amount=20_000_000.0,
            currency="IDR",
            role=role,
            usd_to_idr=16_000.0,
        )
        assert res["role"] == role
        assert len(res["recommended_bundle"]) > 0


def test_calculate_life_energy_hours():
    price = 15_000_000.0  # Rp 15M phone
    monthly_budget = 10_000_000.0  # Rp 10M monthly discretionary

    res = calculate_life_energy_hours(
        price=price,
        monthly_discretionary_budget=monthly_budget,
        hours_per_month=160.0,
    )

    # Hourly rate = 10M / 160 = 62,500 Rp/hr
    # Hours worked = 15M / 62,500 = 240.0 hours
    # Working days = 240 / 8 = 30.0 days
    assert res["hourly_discretionary_rate"] == 62_500.0
    assert res["life_energy_hours"] == 240.0
    assert res["life_energy_work_days"] == 30.0


def test_api_quant_opportunity_cost_endpoint():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    payload = {
        "principal": 15000000.0,
        "currency": "IDR",
        "role": "tech_software",
        "age_bracket": "early_career",
        "monthly_budget": 8000000.0,
        "annual_rate": 0.06,
    }
    resp = client.post("/api/v1/quant/opportunity-cost", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert data["compounding"]["principal"] == 15000000.0
    assert len(data["human_capital"]["recommended_bundle"]) > 0
    assert data["life_energy"]["life_energy_hours"] > 0


def test_api_bank_divert_to_growth_pot_endpoint():
    from fastapi.testclient import TestClient
    from app.main import app
    from app.bank.service import bank_service

    # Ensure sufficient checking balance
    bank_service.deposit_income(amount_idr=10_000_000.0, source="Test Income Deposit")

    client = TestClient(app)
    payload = {
        "amount": 2500000.0,
        "currency": "IDR",
        "item_name": "Test Gadget Impulse",
        "growth_target": "AWS Cloud Architect Pot",
        "user_id": "USR_DEFAULT",
    }
    resp = client.post("/api/v1/bank/divert-to-growth-pot", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert data["diverted_amount"] == 2500000.0
    assert data["growth_pot_balance"] >= 2500000.0


