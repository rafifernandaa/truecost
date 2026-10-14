import numpy as np
from typing import List, Dict, Any, Optional
import re
from urllib.parse import urlparse

# Suspicious TLDs and scam pattern keywords
SUSPICIOUS_TLDS = {".xyz", ".top", ".store", ".live", ".shop", ".click", ".vip", ".loan"}
LEGIT_PLATFORMS = {"tokopedia.com", "shopee.co.id", "blibli.com", "ebay.com", "ebay.com.au", "amazon.com", "amazon.com.au"}

def compute_robust_z_score(price: float, market_prices: List[float]) -> float:
    """
    Computes Boris Iglewicz and David Hoaglin's Modified Z-score based on
    Median and Median Absolute Deviation (MAD).
    Robust against skewed e-commerce distributions and extreme outliers.
    """
    if not market_prices or len(market_prices) < 3:
        return 0.0

    prices = np.array(market_prices, dtype=float)
    median = np.median(prices)
    mad = np.median(np.abs(prices - median))

    if mad == 0.0:
        # If all or most prices are identical, check deviation from median
        diff = price - median
        if diff == 0.0:
            return 0.0
        return float(diff / (0.1 * median))

    # 0.6745 is the consistency factor for normal distributions
    modified_z = 0.6745 * (price - median) / mad
    return float(modified_z)


def analyze_scam_risk(
    listing_price: float,
    market_prices: List[float],
    seller_feedback_score: Optional[float] = 98.0,  # e.g. 98.5% positive
    seller_review_count: Optional[int] = 150,
    seller_account_age_days: Optional[int] = 365,
    listing_url: Optional[str] = None,
    demands_off_platform_payment: bool = False
) -> Dict[str, Any]:
    """
    Evaluates a listing against statistical price distributions and seller/domain fraud markers.
    Returns a unified scam risk score (0.0 to 1.0) and triggers the Revolut-style Scam Intervention Flow.
    """
    reasons: List[str] = []
    risk_points = 0.0
    max_points = 100.0

    # 1. Price Anomaly (Weight: 45 pts)
    mod_z = compute_robust_z_score(listing_price, market_prices)
    if mod_z < -3.5:
        risk_points += 45.0
        reasons.append(
            f"CRITICAL: Price ({listing_price:,.2f}) is an extreme statistical anomaly "
            f"(Modified z-score: {mod_z:.2f}). Far below market median."
        )
    elif mod_z < -2.2:
        risk_points += 25.0
        reasons.append(f"WARNING: Price is substantially below normal market distribution (z: {mod_z:.2f}).")

    # 2. Demands Off-Platform Payment (Weight: 35 pts)
    if demands_off_platform_payment:
        risk_points += 35.0
        reasons.append("CRITICAL: Seller attempts to bypass platform escrow or demands wire/gift card/crypto.")

    # 3. Seller History & Reputation (Weight: 20 pts)
    if seller_account_age_days is not None and seller_account_age_days < 30:
        risk_points += 10.0
        reasons.append(f"SUSPICIOUS: Seller account is freshly created ({seller_account_age_days} days old).")

    if seller_review_count is not None and seller_review_count < 5:
        risk_points += 5.0
        reasons.append(f"CAUTION: Very low transaction history ({seller_review_count} reviews).")

    if seller_feedback_score is not None and seller_feedback_score < 85.0:
        risk_points += 10.0
        reasons.append(f"POOR_REPUTATION: Low seller rating ({seller_feedback_score}%).")

    # 4. Domain & URL Analysis (Weight: 15 pts)
    if listing_url:
        parsed = urlparse(listing_url)
        domain = parsed.netloc.lower()
        if any(domain.endswith(tld) for tld in SUSPICIOUS_TLDS):
            risk_points += 15.0
            reasons.append(f"SUSPICIOUS_DOMAIN: Website uses high-risk fraud TLD ({domain}).")

        # Lookalike / Typo-squatting detection
        for legit in LEGIT_PLATFORMS:
            # Check if domain mimics legit platform name but is not the legit platform
            if legit.split('.')[0] in domain and not domain.endswith(legit):
                risk_points += 20.0
                reasons.append(f"TYPOSQUATTING: Domain '{domain}' mimics authorized platform '{legit}'.")
                break

    scam_score = min(1.0, risk_points / max_points)
    triggers_intervention = scam_score >= 0.50

    return {
        "listing_price": listing_price,
        "modified_z_score": round(mod_z, 2),
        "scam_score": round(scam_score, 3),
        "risk_level": "CRITICAL" if scam_score >= 0.7 else "HIGH" if scam_score >= 0.5 else "MEDIUM" if scam_score >= 0.25 else "LOW",
        "triggers_scam_intervention": triggers_intervention,
        "reasons": reasons,
        "recommended_action": "BLOCK_AND_WARN" if triggers_intervention else "PROCEED_SAFE"
    }
