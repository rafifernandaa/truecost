import pytest
from app.engine.topsis import rank_alternatives_topsis


def test_topsis_ranking():
    candidates = [
        {"id": "laptop_a", "price": 18000000.0, "ram_gb": 16.0, "weight_kg": 1.4, "rating": 4.8},
        {"id": "laptop_b", "price": 14000000.0, "ram_gb": 8.0, "weight_kg": 2.1, "rating": 4.2},
        {"id": "laptop_c", "price": 16500000.0, "ram_gb": 16.0, "weight_kg": 1.3, "rating": 4.9},
    ]

    weights = {
        "price": 0.35,
        "ram_gb": 0.30,
        "weight_kg": 0.15,
        "rating": 0.20
    }

    types = {
        "price": "cost",       # lower is better
        "ram_gb": "benefit",   # higher is better
        "weight_kg": "cost",   # lower is better
        "rating": "benefit"    # higher is better
    }

    ranked = rank_alternatives_topsis(candidates, weights, types)

    assert len(ranked) == 3
    assert ranked[0]["topsis_rank"] == 1
    assert ranked[0]["topsis_score"] >= ranked[1]["topsis_score"]
    # Laptop C is lightweight, high ram, excellent rating, reasonable price -> should beat Laptop B
    assert any(item["id"] == "laptop_c" for item in ranked[:2])
