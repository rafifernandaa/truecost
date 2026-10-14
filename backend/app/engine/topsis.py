import numpy as np
from typing import List, Dict, Any


def rank_alternatives_topsis(
    candidates: List[Dict[str, Any]],
    criteria_weights: Dict[str, float],
    criteria_types: Dict[str, str]  # "benefit" (higher is better) or "cost" (lower is better)
) -> List[Dict[str, Any]]:
    """
    Ranks product alternatives using the deterministic TOPSIS algorithm.
    candidates: list of dicts with 'id', 'name', and numerical criteria keys.
    criteria_weights: relative importance of each metric (sums to 1.0)
    criteria_types: whether higher is better ("benefit") or lower is better ("cost")
    """
    if not candidates:
        return []

    if len(candidates) == 1:
        c = candidates[0].copy()
        c["topsis_score"] = 1.0
        c["rank"] = 1
        return [c]

    criteria_keys = list(criteria_weights.keys())
    m = len(candidates)
    n = len(criteria_keys)

    # 1. Build Decision Matrix X
    matrix = np.zeros((m, n), dtype=float)
    for i, item in enumerate(candidates):
        for j, crit in enumerate(criteria_keys):
            matrix[i, j] = float(item.get(crit, 0.0))

    # 2. Vector Normalization
    col_norms = np.linalg.norm(matrix, axis=0)
    col_norms[col_norms == 0.0] = 1.0  # avoid division by zero
    norm_matrix = matrix / col_norms

    # 3. Weighted Normalized Decision Matrix
    weights = np.array([criteria_weights[k] for k in criteria_keys], dtype=float)
    weights = weights / np.sum(weights)  # normalize weights
    weighted_matrix = norm_matrix * weights

    # 4. Determine Positive Ideal Solution (A+) and Negative Ideal Solution (A-)
    a_pos = np.zeros(n)
    a_neg = np.zeros(n)

    for j, crit in enumerate(criteria_keys):
        c_type = criteria_types.get(crit, "benefit")
        if c_type == "benefit":
            a_pos[j] = np.max(weighted_matrix[:, j])
            a_neg[j] = np.min(weighted_matrix[:, j])
        else:  # "cost"
            a_pos[j] = np.min(weighted_matrix[:, j])
            a_neg[j] = np.max(weighted_matrix[:, j])

    # 5. Calculate Euclidean Distances to A+ and A-
    dist_pos = np.sqrt(np.sum((weighted_matrix - a_pos) ** 2, axis=1))
    dist_neg = np.sqrt(np.sum((weighted_matrix - a_neg) ** 2, axis=1))

    # 6. Relative Closeness to Ideal Solution (C_i)
    total_dist = dist_pos + dist_neg
    total_dist[total_dist == 0.0] = 1.0
    closeness = dist_neg / total_dist

    # 7. Sort and assign ranks
    ranked_indices = np.argsort(-closeness)  # Descending order

    results = []
    for rank, idx in enumerate(ranked_indices, start=1):
        item_copy = candidates[idx].copy()
        item_copy["topsis_score"] = round(float(closeness[idx]), 4)
        item_copy["topsis_rank"] = rank
        item_copy["dist_to_ideal"] = round(float(dist_pos[idx]), 4)
        results.append(item_copy)

    return results
