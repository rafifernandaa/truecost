import pytest
from app.engine.scam_detector import (
    compute_robust_z_score,
    analyze_scam_risk,
    validate_imei_luhn,
    validate_gstin,
    validate_abn,
    validate_npwp,
    reconcile_invoice_line_items,
    parse_invoice_text,
    audit_invoice_authenticity,
)


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


def test_real_samsung_s23_invoice_authenticity_audit():
    """
    Forensic audit against real Samsung Galaxy S23 5G Tax Invoice
    (CIGFIL Limited / Flipkart, ₹38,999, GSTIN 27AAACC3120C1ZH, IMEI 351824514364684).
    """
    s23_invoice = {
        "seller_name": "CIGFIL Limited",
        "platform": "Flipkart",
        "gstin": "27AAACC3120C1ZH",
        "seller_pan": "AAACC3120C",
        "irn": "d4ed4e00e98ff0a9af07cc6ddb927ded4e864717aa83a297baf0df8088a6266f",
        "invoice_number": "FAJGKD2500469403",
        "order_id": "OD332973924345662100",
        "imei": "351824514364684",
        "hsn_sac": "85171300",
        "taxable_value": 33050.00,
        "tax_components": [2974.50, 2974.50],
        "shipping_fee": 40.00,
        "discounts": 40.00,
        "claimed_total": 38999.00,
    }

    # Market prices for Samsung Galaxy S23 (128GB) during festive sale: ₹37,999 - ₹44,999
    market_inr = [37999.0, 38999.0, 39999.0, 41999.0, 44999.0]

    audit = audit_invoice_authenticity(s23_invoice, market_prices=market_inr)

    assert audit["is_authentic_invoice"] is True
    assert audit["verdict"] == "AUTHENTIC_ORIGINAL_INVOICE"
    assert audit["authenticity_score"] >= 0.90
    assert audit["scam_score"] == 0.0
    assert audit["imei_luhn_valid"] is True
    assert audit["gstin_validation"]["is_valid"] is True
    assert audit["gstin_validation"]["pan"] == "AAACC3120C"
    assert audit["gstin_validation"]["state_code"] == "27"
    assert len(audit["fraud_flags"]) == 0
    assert any("VALID_IMEI_LUHN" in m for m in audit["trust_markers"])
    assert any("VALID_64CHAR_SHA256_E_INVOICE_IRN" in m for m in audit["trust_markers"])
    assert any("MATHEMATICALLY_RECONCILED_LINE_ITEMS" in m for m in audit["trust_markers"])

    # Integrated risk evaluation with authentic invoice attached
    risk = analyze_scam_risk(
        listing_price=38999.0,
        market_prices=market_inr,
        seller_feedback_score=98.0,
        invoice_data=s23_invoice,
    )
    assert risk["risk_level"] == "LOW"
    assert not risk["triggers_scam_intervention"]
    assert risk["recommended_action"] == "PROCEED_SAFE"
    assert "invoice_audit" in risk
    assert risk["invoice_audit"]["is_authentic_invoice"] is True


def test_fake_counterfeit_samsung_invoice_caught():
    """
    Forensic audit catches a forged scam invoice:
    - Counterfeit IMEI failing Luhn checksum
    - Malformed GSTIN
    - Altered arithmetic where claimed total doesn't reconcile
    - Off-platform direct wire transfer demand
    """
    fake_invoice = {
        "seller_name": "Shady Telecom Deals",
        "platform": "Telegram Store",
        "gstin": "INVALID-GST-NUMBER",
        "irn": "short_fake_irn_123",
        "imei": "351824514364689",  # Tampered last digit, FAILS Luhn!
        "taxable_value": 10000.00,
        "tax_components": [500.00],
        "claimed_total": 12999.00,  # Math discrepancy: 10000 + 500 = 10500 != 12999!
    }

    audit = audit_invoice_authenticity(fake_invoice)

    assert audit["is_authentic_invoice"] is False
    assert audit["verdict"] == "FRAUDULENT_FABRICATED_INVOICE"
    assert audit["imei_luhn_valid"] is False
    assert any("INVALID_IMEI_LUHN" in f for f in audit["fraud_flags"])
    assert any("INVALID_GSTIN" in f for f in audit["fraud_flags"])
    assert any("ARITHMETIC_MISMATCH" in f for f in audit["fraud_flags"])
    assert any("MALFORMED_IRN" in f for f in audit["fraud_flags"])

    # Integrated scam risk triggers Tier 3 intervention
    risk = analyze_scam_risk(
        listing_price=12999.0,
        market_prices=[38000.0, 39000.0, 42000.0],
        invoice_data=fake_invoice,
        demands_off_platform_payment=True,
    )
    assert risk["triggers_scam_intervention"] is True
    assert risk["risk_level"] == "CRITICAL"
    assert risk["recommended_action"] == "BLOCK_AND_WARN"


def test_australian_invoice_abn_and_indonesian_npwp_audit():
    """
    Validates cross-border tax invoices for Australia (ABN modulo 89) and Indonesia (NPWP).
    """
    # Telstra ABN: 33 051 775 556
    assert validate_abn("33 051 775 556") is True
    # Tampered ABN
    assert validate_abn("33 051 775 557") is False

    # Indonesian NPWP
    assert validate_npwp("01.300.200.4-051.000") is True
    assert validate_npwp("123") is False

    aus_invoice = {
        "seller_name": "JB Hi-Fi Australia",
        "platform": "JB Hi-Fi",
        "abn": "33 051 775 556",
        "taxable_value": 1000.0,
        "tax_components": [100.0],  # 10% Australian GST
        "shipping_fee": 0.0,
        "discounts": 0.0,
        "claimed_total": 1100.0,
    }
    audit = audit_invoice_authenticity(aus_invoice)
    assert audit["is_authentic_invoice"] is True
    assert any("VALID_AUSTRALIAN_ABN" in m for m in audit["trust_markers"])


def test_parse_invoice_text_from_raw_ocr_string():
    """
    Validates regex extraction from the raw text OCR copy of the Samsung S23 invoice.
    """
    raw_ocr = """
    Tax Invoice
    Sold By: CIGFIL Limited ,
    Ship-from Address: Warehouse 4B, Bhiwandi
    GSTIN - 27AAACC3120C1ZH
    IRN - d4ed4e00e98ff0a9af07cc6ddb927ded4e864717aa83a297baf0df8088a6266f
    Invoice Number # FAJGKD2500469403
    Order ID: OD332973924345662100
    Order Date: 29-11-2024
    Invoice Date: 03-12-2024
    PAN: AAACC3120C
    Bill To: Smit Shah ABHINANDAN ENTERPRISE
    Product: SAMSUNG Galaxy S23 5G (Cream, 128 GB)
    FSN: MOBGMFFX5XYE8MZN
    HSN/SAC: 85171300
    IMEI/Serial No: 351824514364684
    Taxable Value: 33,050.00
    CGST 9.0%: 2,974.50
    SGST/UTGST 9.0%: 2,974.50
    Shipping And Packaging Charges: 40.00
    Discounts / Coupons: -40.00
    Grand Total: 38,999.00
    Contact Flipkart: 044 - 66904500
    """
    parsed = parse_invoice_text(raw_ocr)

    assert parsed["gstin"] == "27AAACC3120C1ZH"
    assert parsed["irn"] == "d4ed4e00e98ff0a9af07cc6ddb927ded4e864717aa83a297baf0df8088a6266f"
    assert parsed["imei"] == "351824514364684"
    assert parsed["hsn_sac"] == "85171300"
    assert parsed["order_id"] == "OD332973924345662100"
    assert parsed["invoice_number"] == "FAJGKD2500469403"
    assert parsed["seller_pan"] == "AAACC3120C"
    assert parsed["taxable_value"] == 33050.00
    assert parsed["claimed_total"] == 38999.00
    assert parsed["platform"] == "Flipkart"
    assert "CIGFIL" in parsed["seller_name"]

    audit = audit_invoice_authenticity(parsed)
    assert audit["is_authentic_invoice"] is True
    assert audit["verdict"] == "AUTHENTIC_ORIGINAL_INVOICE"
