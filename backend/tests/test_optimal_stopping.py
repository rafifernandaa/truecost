import pytest
from app.engine.optimal_stopping import compute_reservation_prices, evaluate_buy_timing


def test_reservation_price_decay():
    # Over 14 days, reservation price should relax from deep discount (day 0) towards median (day 13)
    history = [15000000.0, 16000000.0, 16500000.0, 17000000.0, 18000000.0, 19000000.0]
    curve = compute_reservation_prices(history, total_days_horizon=14)

    assert len(curve) == 14
    # Earliest day reservation price should be strictly lower than or equal to last day
    assert curve[0] <= curve[-1]


def test_evaluate_buy_timing_decisions():
    history = [15000000.0, 16000000.0, 16500000.0, 17000000.0, 18000000.0, 19000000.0]

    # Day 2 with an expensive price (18.5M) -> Should WAIT
    wait_res = evaluate_buy_timing(
        current_price=18500000.0,
        price_history=history,
        days_elapsed=2,
        total_deadline_days=14
    )
    assert wait_res["decision"] == "WAIT"

    # Day 2 with a rare deep discount (15.2M) -> Should BUY
    buy_res = evaluate_buy_timing(
        current_price=15200000.0,
        price_history=history,
        days_elapsed=2,
        total_deadline_days=14
    )
    assert buy_res["decision"] == "BUY"
