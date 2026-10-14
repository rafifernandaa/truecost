import numpy as np
from typing import List, Dict, Any
from app.engine.optimal_stopping import compute_reservation_prices, evaluate_buy_timing


def run_time_travel_simulation(
    price_series: List[float],
    total_days_horizon: int = 14,
    item_title: str = "Lenovo ThinkPad T14s Gen 4"
) -> Dict[str, Any]:
    """
    Simulates and benchmarks the TrueCost Autopilot agent against traditional baselines:
    1. Baseline A (Naive): Buy immediately on Day 0.
    2. Baseline B (Greedy): Buy at first discount (>2% drop from day 0).
    3. TrueCost Autopilot: Finite-horizon optimal stopping via reservation price curve R_t.
    4. Theoretical Oracle: Global minimum price across the entire window (zero regret).
    """
    if not price_series or len(price_series) < 2:
        raise ValueError("Price series must contain at least 2 data points.")

    horizon = min(len(price_series), total_days_horizon)
    active_series = price_series[:horizon]

    # Pre-calculate reservation price curve for the full series
    reservation_curve = compute_reservation_prices(active_series, horizon)

    # 1. Baseline A: Buy Immediately on Day 0
    price_baseline_a = active_series[0]
    day_baseline_a = 0

    # 2. Baseline B: Greedy (First Drop > 2%)
    price_baseline_b = active_series[0]
    day_baseline_b = 0
    for day, p in enumerate(active_series):
        if p <= active_series[0] * 0.98:
            price_baseline_b = p
            day_baseline_b = day
            break
    if day_baseline_b == 0 and len(active_series) > 1:
        # If no discount ever occurred, bought on last day
        price_baseline_b = active_series[-1]
        day_baseline_b = horizon - 1

    # 3. TrueCost Autopilot (Optimal Stopping)
    price_agent = None
    day_agent = None
    agent_decision_steps = []

    for day in range(horizon):
        curr_price = active_series[day]
        eval_res = evaluate_buy_timing(
            current_price=curr_price,
            price_history=active_series,
            days_elapsed=day,
            total_deadline_days=horizon
        )

        step_info = {
            "day": day,
            "current_price": round(curr_price, 2),
            "reservation_price": eval_res["reservation_price"],
            "decision": eval_res["decision"],
            "percentile_rank": eval_res["percentile_rank"],
            "rationale": eval_res["rationale"]
        }
        agent_decision_steps.append(step_info)

        if eval_res["decision"] in ("BUY", "BUY_DEADLINE_REACHED") and price_agent is None:
            price_agent = curr_price
            day_agent = day

    if price_agent is None:
        price_agent = active_series[-1]
        day_agent = horizon - 1

    # 4. Theoretical Oracle (Perfect Hindsight Minimum)
    oracle_min_price = float(np.min(active_series))
    oracle_day = int(np.argmin(active_series))

    # Performance Metrics
    savings_vs_naive = price_baseline_a - price_agent
    savings_vs_naive_pct = (savings_vs_naive / price_baseline_a) * 100.0

    savings_vs_greedy = price_baseline_b - price_agent
    savings_vs_greedy_pct = (savings_vs_greedy / price_baseline_b) * 100.0

    regret_vs_oracle = price_agent - oracle_min_price
    regret_vs_oracle_pct = (regret_vs_oracle / oracle_min_price) * 100.0

    return {
        "item_title": item_title,
        "total_days_horizon": horizon,
        "price_series": [round(p, 2) for p in active_series],
        "reservation_curve": reservation_curve,
        "steps": agent_decision_steps,
        "results": {
            "agent": {
                "strategy": "TrueCost Autopilot (Optimal Stopping)",
                "execution_day": day_agent,
                "price_paid": round(price_agent, 2),
            },
            "baseline_a": {
                "strategy": "Naive (Buy Day 0)",
                "execution_day": day_baseline_a,
                "price_paid": round(price_baseline_a, 2),
            },
            "baseline_b": {
                "strategy": "Greedy (First Discount > 2%)",
                "execution_day": day_baseline_b,
                "price_paid": round(price_baseline_b, 2),
            },
            "oracle": {
                "strategy": "Theoretical Oracle (Perfect Hindsight)",
                "execution_day": oracle_day,
                "price_paid": round(oracle_min_price, 2),
            }
        },
        "benchmarks": {
            "savings_vs_naive_idr": round(savings_vs_naive, 2),
            "savings_vs_naive_pct": round(savings_vs_naive_pct, 2),
            "savings_vs_greedy_idr": round(savings_vs_greedy, 2),
            "savings_vs_greedy_pct": round(savings_vs_greedy_pct, 2),
            "regret_vs_oracle_idr": round(regret_vs_oracle, 2),
            "regret_vs_oracle_pct": round(regret_vs_oracle_pct, 2)
        }
    }
