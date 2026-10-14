import pytest
from app.engine.replay_simulator import run_time_travel_simulation


def test_time_travel_simulation_basic():
    # 14 days of realistic price fluctuations around 18M IDR
    # Day 0: 18.5M (Sticker)
    # Day 1: 18.2M (1.6% drop)
    # Day 2: 17.9M (3.2% drop -> Greedy buys here)
    # Day 3: 18.1M
    # Day 4: 17.5M
    # Day 5: 16.4M (Deep 11.3% drop -> TrueCost Autopilot buys here)
    # Day 6: 17.0M
    # Day 7: 17.3M
    # Day 8: 16.2M (Global Minimum -> Oracle buys here)
    # Day 9: 16.8M
    # Day 10: 17.4M
    # Day 11: 17.9M
    # Day 12: 18.2M
    # Day 13: 18.6M
    prices = [
        18500000.0, 18200000.0, 17900000.0, 18100000.0,
        17500000.0, 16400000.0, 17000000.0, 17300000.0,
        16200000.0, 16800000.0, 17400000.0, 17900000.0,
        18200000.0, 18600000.0
    ]

    sim = run_time_travel_simulation(prices, total_days_horizon=14)

    assert sim["total_days_horizon"] == 14
    assert len(sim["steps"]) == 14

    # Baseline A bought on Day 0 at 18.5M
    assert sim["results"]["baseline_a"]["execution_day"] == 0
    assert sim["results"]["baseline_a"]["price_paid"] == 18500000.0

    # Baseline B bought on Day 2 (first drop > 2%) at 17.9M
    assert sim["results"]["baseline_b"]["execution_day"] == 2
    assert sim["results"]["baseline_b"]["price_paid"] == 17900000.0

    # Agent bought during deep dip at 16.4M
    assert sim["results"]["agent"]["price_paid"] <= 16500000.0

    # Agent saved substantial money compared to naive and greedy
    assert sim["benchmarks"]["savings_vs_naive_idr"] > 1000000.0
    assert sim["benchmarks"]["savings_vs_greedy_idr"] > 500000.0

    # Oracle is 16.2M on Day 8
    assert sim["results"]["oracle"]["execution_day"] == 8
    assert sim["results"]["oracle"]["price_paid"] == 16200000.0
    assert sim["benchmarks"]["regret_vs_oracle_pct"] < 5.0  # minimal regret
