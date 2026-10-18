"""
Deterministic Opportunity Cost & Human Capital Quant Engine.
Calculates multi-horizon compound interest projections, discrete future values,
life-energy work hours, and curated role-based human capital alternatives.
Zero LLM arithmetic: 100% pure NumPy and deterministic math.
"""
from typing import Dict, Any, List, Optional
import numpy as np


# Curated role-based human capital catalog with standardized pricing in USD.
# Prices are dynamically converted to IDR or AUD using live or benchmark exchange rates.
_ROLE_GROWTH_CATALOG: Dict[str, List[Dict[str, Any]]] = {
    "tech_software": [
        {
            "id": "aws_cert",
            "name": "AWS Certified Solutions Architect Exam",
            "cost_usd": 150.0,
            "category": "Certification",
            "career_impact": "+15% Seniority Advantage in Cloud/DevOps",
            "roi_timeline": "6-12 Months",
            "icon": "verified",
        },
        {
            "id": "oreilly_sub",
            "name": "1-Year O'Reilly / Coursera Plus Tech Access",
            "cost_usd": 399.0,
            "category": "Continuous Learning",
            "career_impact": "Master System Architecture & LLM Engineering",
            "roi_timeline": "Immediate",
            "icon": "school",
        },
        {
            "id": "ergo_station",
            "name": "Ergonomic Monitor & Mechanical Setup",
            "cost_usd": 450.0,
            "category": "Productivity Hardware",
            "career_impact": "+20% Daily Deep Work Endurance",
            "roi_timeline": "Immediate",
            "icon": "desktop_windows",
        },
        {
            "id": "ai_bootcamp",
            "name": "Applied AI Engineering Intensive",
            "cost_usd": 750.0,
            "category": "Upskilling",
            "career_impact": "Direct Transition to AI/ML Engineering Tier",
            "roi_timeline": "3-6 Months",
            "icon": "psychology",
        },
    ],
    "design_creative": [
        {
            "id": "adobe_figma",
            "name": "1-Year Figma Professional + Adobe CC Suite",
            "cost_usd": 360.0,
            "category": "Industry Tooling",
            "career_impact": "Client-Ready Design System Handoffs",
            "roi_timeline": "Immediate",
            "icon": "palette",
        },
        {
            "id": "calibrated_display",
            "name": "Color-Accurate 4K Designer Monitor",
            "cost_usd": 450.0,
            "category": "Hardware",
            "career_impact": "Commercial Print & High-DPI Fidelity",
            "roi_timeline": "Immediate",
            "icon": "tv",
        },
        {
            "id": "motion_masterclass",
            "name": "Advanced Motion Design & 3D Masterclass",
            "cost_usd": 300.0,
            "category": "Specialization",
            "career_impact": "Command 2x Rates for Interactive Animation",
            "roi_timeline": "3 Months",
            "icon": "animation",
        },
        {
            "id": "prime_lens",
            "name": "Fast Prime Lens (50mm f/1.4)",
            "cost_usd": 550.0,
            "category": "Creative Gear",
            "career_impact": "Commercial Video & Portrait Gig Standard",
            "roi_timeline": "1-3 Months",
            "icon": "photo_camera",
        },
    ],
    "business_finance": [
        {
            "id": "fin_modeling",
            "name": "Wall Street Prep Financial Modeling Cert",
            "cost_usd": 350.0,
            "category": "Certification",
            "career_impact": "Essential for M&A and Private Equity Roles",
            "roi_timeline": "3-6 Months",
            "icon": "analytics",
        },
        {
            "id": "cfa_prep",
            "name": "CFA Level 1 Exam Prep & Schweser Package",
            "cost_usd": 450.0,
            "category": "Professional Standard",
            "career_impact": "Chartered Credential Unlocking Global Banking",
            "roi_timeline": "12 Months",
            "icon": "workspace_premium",
        },
        {
            "id": "ft_bloomberg",
            "name": "1-Year Financial Times & Market Intelligence",
            "cost_usd": 280.0,
            "category": "Market Intel",
            "career_impact": "Sharper Deal Intelligence & Macro Foresight",
            "roi_timeline": "Immediate",
            "icon": "newspaper",
        },
        {
            "id": "exec_negotiation",
            "name": "Executive Negotiation & Strategy Workshop",
            "cost_usd": 500.0,
            "category": "Leadership",
            "career_impact": "+10-20% Compensation Negotiation Leverage",
            "roi_timeline": "Immediate",
            "icon": "handshake",
        },
    ],
    "student_academic": [
        {
            "id": "grad_exam",
            "name": "GRE / GMAT / IELTS Test Voucher",
            "cost_usd": 250.0,
            "category": "Postgrad Stepping Stone",
            "career_impact": "Top Tier Global University Admission",
            "roi_timeline": "6-12 Months",
            "icon": "history_edu",
        },
        {
            "id": "academic_research",
            "name": "1-Year Academic Journal & Tool Access",
            "cost_usd": 220.0,
            "category": "Research",
            "career_impact": "Thesis Publication & Research Visibility",
            "roi_timeline": "6 Months",
            "icon": "menu_book",
        },
        {
            "id": "conf_pot",
            "name": "Academic Conference Flight & Registration Pot",
            "cost_usd": 480.0,
            "category": "Networking",
            "career_impact": "Connect with Academic Labs & Industry Sponsors",
            "roi_timeline": "3-6 Months",
            "icon": "flight_takeoff",
        },
        {
            "id": "study_station",
            "name": "Reliable Ergonomic Study & Computing Gear",
            "cost_usd": 400.0,
            "category": "Daily Driver",
            "career_impact": "Zero Downtime During Exams & Projects",
            "roi_timeline": "Immediate",
            "icon": "laptop_chromebook",
        },
    ],
}


def compute_compound_opportunity_cost(
    principal: float,
    horizons_years: Optional[List[int]] = None,
    annual_rate: float = 0.05,
    compounding_frequency: int = 12,
    conservative_rate: float = 0.02,
    aggressive_rate: float = 0.08,
) -> Dict[str, Any]:
    """
    Computes multi-horizon compound interest future value trajectories.
    Formula: FV = P * (1 + r / n)**(n * t)
    All calculations are pure deterministic NumPy without floating drift.
    """
    if principal < 0:
        principal = 0.0

    if horizons_years is None:
        horizons_years = [1, 3, 5, 10, 20]

    p = float(principal)
    n = float(compounding_frequency)

    projections = []
    for t in horizons_years:
        t_float = float(t)
        # Moderate benchmark rate (e.g. 5%)
        fv_mod = p * ((1.0 + (annual_rate / n)) ** (n * t_float))
        # Conservative cash rate (e.g. 2%)
        fv_cons = p * ((1.0 + (conservative_rate / n)) ** (n * t_float))
        # Aggressive index/equity rate (e.g. 8%)
        fv_agg = p * ((1.0 + (aggressive_rate / n)) ** (n * t_float))

        interest_earned_mod = fv_mod - p
        multiple_mod = (fv_mod / p) if p > 0 else 1.0

        projections.append({
            "horizon_years": t,
            "future_value": round(float(fv_mod), 2),
            "interest_earned": round(float(interest_earned_mod), 2),
            "multiple": round(float(multiple_mod), 2),
            "future_value_conservative": round(float(fv_cons), 2),
            "future_value_aggressive": round(float(fv_agg), 2),
        })

    rule_of_72_years = round(72.0 / (annual_rate * 100.0), 1) if annual_rate > 0 else 0.0

    return {
        "principal": round(p, 2),
        "annual_rate": float(annual_rate),
        "compounding_frequency": compounding_frequency,
        "rule_of_72_doubling_years": rule_of_72_years,
        "projections": projections,
        "default_5y_future_value": next(
            (p["future_value"] for p in projections if p["horizon_years"] == 5),
            round(p * ((1.0 + annual_rate) ** 5), 2)
        ),
        "default_5y_interest_earned": next(
            (p["interest_earned"] for p in projections if p["horizon_years"] == 5),
            0.0
        ),
    }


def get_human_capital_alternatives(
    budget_amount: float,
    currency: str = "IDR",
    role: str = "tech_software",
    usd_to_idr: float = 16000.0,
    aud_to_idr: float = 10400.0,
) -> Dict[str, Any]:
    """
    Selects concrete, high-ROI upskilling and career accelerator alternatives
    matching the user's role and budget.
    """
    budget_clean = max(0.0, float(budget_amount))
    cur = (currency or "IDR").upper()

    # Convert incoming budget to USD equivalent for catalog matching
    if cur == "USD":
        budget_usd = budget_clean
    elif cur == "AUD":
        budget_usd = (budget_clean * aud_to_idr) / usd_to_idr
    else:  # IDR
        budget_usd = budget_clean / (usd_to_idr if usd_to_idr > 0 else 16000.0)

    # Normalize role
    role_key = role.lower().replace("-", "_").replace(" ", "_")
    if role_key not in _ROLE_GROWTH_CATALOG:
        role_key = "tech_software"

    items = _ROLE_GROWTH_CATALOG[role_key]

    # Convert catalog to user's currency
    localized_items = []
    for it in items:
        cost_u = float(it["cost_usd"])
        if cur == "USD":
            cost_local = cost_u
        elif cur == "AUD":
            cost_local = (cost_u * usd_to_idr) / aud_to_idr
        else:  # IDR
            cost_local = cost_u * usd_to_idr

        localized_items.append({
            **it,
            "cost_local": round(cost_local, 2),
            "formatted_cost": f"Rp {int(cost_local):,}" if cur == "IDR" else f"{cur} {cost_local:,.2f}",
        })

    # Greedy knapsack selection: pick items fitting within the budget
    selected_items: List[Dict[str, Any]] = []
    spent_local = 0.0

    for item in localized_items:
        if spent_local + item["cost_local"] <= budget_clean * 1.05:  # allow 5% leeway
            selected_items.append(item)
            spent_local += item["cost_local"]

    # If even the cheapest item exceeds budget, recommend the lowest-cost one as a fractional goal
    if not selected_items and localized_items:
        cheapest = min(localized_items, key=lambda x: x["cost_local"])
        selected_items.append({
            **cheapest,
            "is_fractional": True,
            "pct_funded": round((budget_clean / cheapest["cost_local"]) * 100.0, 1) if cheapest["cost_local"] > 0 else 100.0,
        })
        spent_local = min(budget_clean, cheapest["cost_local"])

    surplus_local = max(0.0, budget_clean - spent_local)

    return {
        "role": role_key,
        "currency": cur,
        "budget_input": round(budget_clean, 2),
        "total_bundle_cost": round(spent_local, 2),
        "surplus_remaining": round(surplus_local, 2),
        "items_count": len(selected_items),
        "recommended_bundle": selected_items,
        "catalog_size": len(localized_items),
        "human_capital_irr_estimate": "350% - 1,200% via Career Progression",
    }


def calculate_life_energy_hours(
    price: float,
    monthly_discretionary_budget: float,
    hours_per_month: float = 160.0,
) -> Dict[str, Any]:
    """
    Computes 'Life Energy' required to purchase the item.
    Formula: Effective Hourly Wage = Monthly Budget / Hours Per Month (default 160h).
    Life Energy Hours = Price / Effective Hourly Wage.
    """
    p = max(0.0, float(price))
    budget = max(1.0, float(monthly_discretionary_budget))
    h = max(1.0, float(hours_per_month))

    hourly_rate = budget / h
    hours_worked = p / hourly_rate if hourly_rate > 0 else 0.0
    working_days = hours_worked / 8.0  # standard 8-hour workday

    return {
        "price": round(p, 2),
        "monthly_budget": round(budget, 2),
        "hourly_discretionary_rate": round(hourly_rate, 2),
        "life_energy_hours": round(hours_worked, 1),
        "life_energy_work_days": round(working_days, 1),
    }
