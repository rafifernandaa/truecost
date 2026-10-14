import pytest
from app.engine.scam_detector import compute_robust_z_score, analyze_scam_risk


def test_normal_market_price():
    # Market prices around 18M IDR (laptop)
    market = [17500000.0, 18000000.0, 18200000.0, 18500000.0, 17900000.0]
    listing = 17800000.0

    risk = analyze_scam_risk(
        listing_price=listing,
        market_prices=market,
        seller_feedback_score=99.0,
        seller_review_count=500,
        seller_account_age_days=700,
        listing_url="https://www.tokopedia.com/official-store/laptop"
    )

    assert risk["risk_level"] == "LOW"
    assert not risk["triggers_scam_intervention"]
    assert risk["recommended_action"] == "PROCEED_SAFE"


def test_extreme_low_outlier_scam_with_fake_domain():
    # Laptop is normally 18M IDR, but scammer lists for 4M IDR on a sketchy domain
    market = [17500000.0, 18000000.0, 18200000.0, 18500000.0, 17900000.0]
    scam_listing = 4000000.0  # ~78% below median!

    risk = analyze_scam_risk(
        listing_price=scam_listing,
        market_prices=market,
        seller_feedback_score=60.0,
        seller_review_count=1,
        seller_account_age_days=4,
        listing_url="https://tokopedia-promo-murah.xyz/item",
        demands_off_platform_payment=True
    )

    assert risk["modified_z_score"] < -3.5
    assert risk["triggers_scam_intervention"]
    assert risk["risk_level"] == "CRITICAL"
    assert risk["recommended_action"] == "BLOCK_AND_WARN"
    assert any("CRITICAL: Price" in r for r in risk["reasons"])
    assert any("TYPOSQUATTING" in r for r in risk["reasons"])
