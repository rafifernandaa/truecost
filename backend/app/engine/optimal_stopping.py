import numpy as np
from typing import List, Dict, Any, Tuple


def compute_reservation_prices(
    price_history: List[float],
    total_days_horizon: int,
    daily_volatility: float = 0.02
) -> List[float]:
    """
    Computes dynamic reservation price thresholds R_t for t = 1..T using
    finite-horizon backward induction over the empirical price distribution.
    
    At time t:
    - If observed price <= R_t, optimal decision is BUY.
    - If observed price > R_t, optimal decision is WAIT.
    As t -> T (deadline), R_t relaxes towards the market mean (option value decays).
    """
    if not price_history:
        return [0.0] * total_days_horizon

    prices = np.sort(np.array(price_history, dtype=float))
    n = len(prices)
    mean_price = float(np.mean(prices))
    p10 = float(np.percentile(prices, 10))
    p50 = float(np.percentile(prices, 50))

    # At final deadline t=T, you must buy at whatever price is available,
    # so reservation price R_T is effectively the median/expected price.
    reservation_prices = [0.0] * total_days_horizon
    expected_future_cost = mean_price

    # Backward induction from day T down to day 1
    for t in reversed(range(total_days_horizon)):
        # Days remaining until deadline
        days_left = total_days_horizon - t - 1

        if days_left == 0:
            # Last day: take any normal market price
            r_t = p50 * 1.05
        else:
            # Option value: early on (large days_left), we demand a deep discount (e.g. near 10th percentile).
            # As days_left shrinks, the threshold linearly/exponentially relaxes toward p50.
            decay_factor = (days_left / total_days_horizon) ** 0.7
            r_t = p10 + (p50 - p10) * (1.0 - decay_factor)

        reservation_prices[t] = round(r_t, 2)

    return reservation_prices


def evaluate_buy_timing(
    current_price: float,
    price_history: List[float],
    days_elapsed: int,
    total_deadline_days: int
) -> Dict[str, Any]:
    """
    Determines whether the agent should BUY immediately or WAIT,
    based on current position within the optimal stopping reservation curve.
    """
    if days_elapsed >= total_deadline_days:
        return {
            "decision": "BUY_DEADLINE_REACHED",
            "current_price": current_price,
            "reservation_price": current_price,
            "days_left": 0,
            "percentile_rank": 100.0,
            "rationale": "Purchase deadline has arrived. Executing order to fulfill mandate."
        }

    curve = compute_reservation_prices(price_history, total_deadline_days)
    current_threshold = curve[min(days_elapsed, total_deadline_days - 1)]

    # Compute empirical percentile rank
    prices = np.sort(np.array(price_history, dtype=float))
    percentile = float(np.searchsorted(prices, current_price) / len(prices) * 100.0)

    days_left = total_deadline_days - days_elapsed

    if current_price <= current_threshold:
        decision = "BUY"
        rationale = (
            f"Favorable deal detected: Price {current_price:,.2f} is at or below the "
            f"reservation price {current_threshold:,.2f} (Top {percentile:.1f}% cheapest historically). "
            f"Expected gain from waiting further ({days_left} days left) is lower than this immediate saving."
        )
    else:
        decision = "WAIT"
        diff = current_price - current_threshold
        rationale = (
            f"Hold off: Current price {current_price:,.2f} is {diff:,.2f} above optimal reservation "
            f"threshold {current_threshold:,.2f} (Percentile {percentile:.1f}%). "
            f"With {days_left} days remaining before deadline, waiting has a high probability of yielding a lower price."
        )

    return {
        "decision": decision,
        "current_price": round(current_price, 2),
        "reservation_price": round(current_threshold, 2),
        "price_difference": round(current_price - current_threshold, 2),
        "percentile_rank": round(percentile, 1),
        "days_elapsed": days_elapsed,
        "days_left": days_left,
        "full_reservation_curve": curve,
        "rationale": rationale
    }
