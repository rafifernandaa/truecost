import numpy as np
from typing import List, Dict, Any, Optional
import re
from urllib.parse import urlparse

# Suspicious TLDs and scam pattern keywords
SUSPICIOUS_TLDS = {".xyz", ".top", ".store", ".live", ".shop", ".click", ".vip", ".loan"}
LEGIT_PLATFORMS = {
    "tokopedia.com",
    "shopee.co.id",
    "blibli.com",
    "ebay.com",
    "ebay.com.au",
    "amazon.com",
    "amazon.com.au",
    "amazon.in",
    "flipkart.com",
    "samsung.com",
    "apple.com",
    "jbhifi.com.au",
    "bestbuy.com",
}


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


def validate_imei_luhn(imei: str) -> bool:
    """
    Standard GSM/3GPP Luhn (mod 10) check for 15-digit mobile device IMEI numbers.
    Validates physical device authenticity on electronics invoices.
    """
    clean = re.sub(r"\D", "", str(imei or ""))
    if len(clean) != 15:
        return False
    digits = [int(c) for c in clean]
    total = 0
    for i, d in enumerate(digits):
        if i % 2 == 1:
            doubled = d * 2
            total += (doubled // 10) + (doubled % 10)
        else:
            total += d
    return (total % 10) == 0


def validate_gstin(gstin: str) -> Dict[str, Any]:
    """
    Validates statutory Indian Goods and Services Tax Identification Number (GSTIN).
    Structure: 2-digit state code + 10-char PAN + 1 entity code + 'Z' + check char.
    """
    clean = (gstin or "").strip().upper()
    pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
    if not re.match(pattern, clean):
        return {"is_valid": False, "gstin": clean, "reason": "INVALID_GSTIN_FORMAT"}
    state_code = clean[:2]
    pan = clean[2:12]
    return {
        "is_valid": True,
        "gstin": clean,
        "state_code": state_code,
        "pan": pan,
        "entity_number": clean[12],
        "checksum_char": clean[14],
    }


def validate_abn(abn_str: str) -> bool:
    """
    Validates statutory Australian Business Number (ABN) using modulo 89 weighted checksum.
    """
    clean = "".join(c for c in (abn_str or "") if c.isdigit())
    if len(clean) != 11:
        return False
    weights = [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
    digits = [int(d) for d in clean]
    digits[0] -= 1
    total = sum(d * w for d, w in zip(digits, weights))
    return (total % 89) == 0


def validate_npwp(npwp_str: str) -> bool:
    """
    Validates Indonesian Nomor Pokok Wajib Pajak (NPWP) - 15 or 16 digits.
    """
    clean = "".join(c for c in (npwp_str or "") if c.isdigit())
    return len(clean) in (15, 16)


def reconcile_invoice_line_items(
    taxable_value: float,
    tax_components: List[float],
    discounts: float = 0.0,
    shipping_fee: float = 0.0,
    claimed_total: float = 0.0,
    tolerance: float = 0.05,
) -> Dict[str, Any]:
    """
    Verifies internal mathematical consistency of invoice line items.
    Reconciles taxable base + taxes + shipping - discounts against claimed grand total.
    """
    total_tax = sum(float(t) for t in tax_components)
    computed_total = float(taxable_value) + total_tax + float(shipping_fee) - float(discounts)
    delta = abs(computed_total - float(claimed_total))
    reconciled = delta <= tolerance
    return {
        "is_reconciled": reconciled,
        "taxable_value": round(float(taxable_value), 2),
        "total_tax": round(total_tax, 2),
        "shipping_fee": round(float(shipping_fee), 2),
        "discounts": round(float(discounts), 2),
        "computed_total": round(computed_total, 2),
        "claimed_total": round(float(claimed_total), 2),
        "discrepancy": round(delta, 2),
    }


def parse_invoice_text(raw_text: str) -> Dict[str, Any]:
    """
    Extracts structural invoice attributes from OCR/text representations
    of official retail bills and tax invoices (e.g. Samsung S23 Flipkart/Amazon invoice).
    """
    text = raw_text or ""
    extracted: Dict[str, Any] = {}

    # GSTIN extraction
    gstin_m = re.search(r"\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b", text)
    if gstin_m:
        extracted["gstin"] = gstin_m.group(1).upper()

    # IRN (Invoice Reference Number) - 64 hex characters
    irn_m = re.search(r"\b([0-9a-fA-F]{64})\b", text)
    if irn_m:
        extracted["irn"] = irn_m.group(1).lower()

    # IMEI extraction (15 digits)
    imei_m = re.search(r"\b(?:IMEI|Serial\s*No|IMEI/Serial\s*No)[\s:#]*(\d{15})\b", text, re.IGNORECASE)
    if not imei_m:
        imei_m = re.search(r"\b(\d{15})\b", text)
    if imei_m:
        extracted["imei"] = imei_m.group(1)

    # HSN / SAC Code (e.g. 85171300)
    hsn_m = re.search(r"\b(?:HSN|HSN/SAC|SAC)[\s:#]*(\d{4,8})\b", text, re.IGNORECASE)
    if hsn_m:
        extracted["hsn_sac"] = hsn_m.group(1)

    # Order ID (e.g. OD332973924345662100)
    order_m = re.search(r"\b(?:Order\s*ID|Order\s*#)[\s:#]*([A-Za-z0-9_-]{8,30})\b", text, re.IGNORECASE)
    if order_m:
        extracted["order_id"] = order_m.group(1)

    # Invoice Number (e.g. FAJGKD2500469403)
    inv_num_m = re.search(r"\b(?:Invoice\s*Number|Invoice\s*#)[\s:#]*([A-Za-z0-9_-]{6,30})\b", text, re.IGNORECASE)
    if inv_num_m:
        extracted["invoice_number"] = inv_num_m.group(1)

    # PAN extraction
    pan_m = re.search(r"\bPAN[\s:#]*([A-Z]{5}[0-9]{4}[A-Z]{1})\b", text, re.IGNORECASE)
    if pan_m:
        extracted["seller_pan"] = pan_m.group(1).upper()

    # Taxable Value
    taxable_m = re.search(r"\bTaxable\s*Value[\s:#]*[₹$Rp.]?\s*([\d,]+(?:\.\d+)?)\b", text, re.IGNORECASE)
    if taxable_m:
        try:
            extracted["taxable_value"] = float(taxable_m.group(1).replace(",", ""))
        except ValueError:
            pass

    # Grand Total / Total Amount
    total_m = re.search(r"\b(?:Grand\s*Total|Total\s*Amount|Total)[\s:#]*[₹$Rp.]?\s*([\d,]+(?:\.\d+)?)\b", text, re.IGNORECASE)
    if total_m:
        try:
            extracted["claimed_total"] = float(total_m.group(1).replace(",", ""))
        except ValueError:
            pass

    # CGST & SGST or IGST
    cgst_m = re.search(r"\bCGST(?:\s*\d+(?:\.\d+)?%)?[\s:#]*[₹$Rp.]?\s*([\d,]+(?:\.\d+)?)\b", text, re.IGNORECASE)
    sgst_m = re.search(r"\b(?:SGST|UTGST|SGST/UTGST)(?:\s*\d+(?:\.\d+)?%)?[\s:#]*[₹$Rp.]?\s*([\d,]+(?:\.\d+)?)\b", text, re.IGNORECASE)
    igst_m = re.search(r"\bIGST(?:\s*\d+(?:\.\d+)?%)?[\s:#]*[₹$Rp.]?\s*([\d,]+(?:\.\d+)?)\b", text, re.IGNORECASE)
    taxes = []
    if cgst_m:
        try:
            taxes.append(float(cgst_m.group(1).replace(",", "")))
        except ValueError:
            pass
    if sgst_m:
        try:
            taxes.append(float(sgst_m.group(1).replace(",", "")))
        except ValueError:
            pass
    if igst_m:
        try:
            taxes.append(float(igst_m.group(1).replace(",", "")))
        except ValueError:
            pass
    if taxes:
        extracted["tax_components"] = taxes

    # Shipping & Discounts
    ship_m = re.search(r"\b(?:Shipping|Packaging)[\s\w]*[\s:#]*[₹$Rp.]?\s*([\d,]+(?:\.\d+)?)\b", text, re.IGNORECASE)
    if ship_m:
        try:
            extracted["shipping_fee"] = float(ship_m.group(1).replace(",", ""))
        except ValueError:
            pass

    disc_m = re.search(r"\b(?:Discounts?|Coupons?)[\s:#]*[₹$Rp.-]?\s*([\d,]+(?:\.\d+)?)\b", text, re.IGNORECASE)
    if disc_m:
        try:
            extracted["discounts"] = abs(float(disc_m.group(1).replace(",", "")))
        except ValueError:
            pass

    # Platform & Seller
    t_lower = text.lower()
    if "flipkart" in t_lower:
        extracted["platform"] = "Flipkart"
    elif "amazon" in t_lower:
        extracted["platform"] = "Amazon"
    elif "samsung" in t_lower:
        extracted["platform"] = "Samsung"
    elif "jb hi-fi" in t_lower or "jbhifi" in t_lower:
        extracted["platform"] = "JB Hi-Fi"

    seller_m = re.search(r"\bSold\s*By[\s:#]*([A-Za-z0-9\s.,&-]+?)(?:,|\n|Ship-from|GSTIN)", text, re.IGNORECASE)
    if seller_m:
        extracted["seller_name"] = seller_m.group(1).strip()

    return extracted


def audit_invoice_authenticity(
    invoice: Dict[str, Any],
    market_prices: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """
    Fine-tuned forensic audit for original retail/tax invoices (e.g. Samsung S23 bill copy).
    Cross-checks statutory registration, IRN hash, IMEI Luhn algorithm, line-item arithmetic,
    HSN classification, authorized platform/seller identity, and statistical price deviation.
    """
    trust_markers: List[str] = []
    fraud_flags: List[str] = []
    authenticity_points = 0.0
    max_points = 100.0

    # 1. Statutory Tax Identification (GSTIN / ABN / NPWP) - 35 pts
    gstin = invoice.get("gstin")
    abn = invoice.get("abn")
    npwp = invoice.get("npwp")

    if gstin:
        gst_res = validate_gstin(gstin)
        if gst_res["is_valid"]:
            authenticity_points += 35.0
            trust_markers.append(f"VALID_GSTIN_FORMAT ({gst_res['gstin']}, State: {gst_res['state_code']})")
            # Cross-check embedded PAN with seller_pan if provided
            seller_pan = invoice.get("seller_pan") or invoice.get("pan")
            if seller_pan:
                if seller_pan.upper() == gst_res["pan"]:
                    authenticity_points += 10.0
                    trust_markers.append(f"MATCHING_SELLER_PAN_EMBEDDING ({seller_pan})")
                else:
                    fraud_flags.append(f"PAN_MISMATCH: Invoice PAN ({seller_pan}) differs from GSTIN PAN ({gst_res['pan']})")
        else:
            fraud_flags.append(f"INVALID_GSTIN: {gstin}")
    elif abn:
        if validate_abn(abn):
            authenticity_points += 35.0
            trust_markers.append(f"VALID_AUSTRALIAN_ABN ({abn})")
        else:
            fraud_flags.append(f"INVALID_ABN_CHECKSUM: {abn}")
    elif npwp:
        if validate_npwp(npwp):
            authenticity_points += 30.0
            trust_markers.append(f"VALID_INDONESIAN_NPWP ({npwp})")
        else:
            fraud_flags.append(f"INVALID_NPWP_FORMAT: {npwp}")
    else:
        fraud_flags.append("MISSING_STATUTORY_TAX_ID: Invoice lacks verifiable GSTIN, ABN, or NPWP")

    # 2. Government Electronic Invoice Reference Number (IRN) - 15 pts
    irn = invoice.get("irn")
    if irn:
        clean_irn = str(irn).strip().lower()
        if len(clean_irn) == 64 and re.match(r"^[0-9a-f]{64}$", clean_irn):
            authenticity_points += 15.0
            trust_markers.append("VALID_64CHAR_SHA256_E_INVOICE_IRN")
        else:
            fraud_flags.append(f"MALFORMED_IRN: Expected 64-char SHA-256 hex string, got {len(clean_irn)} chars")

    # 3. Hardware Asset Serial Number / IMEI Luhn Check - 15 pts
    imei = invoice.get("imei") or invoice.get("serial_number")
    if imei:
        clean_imei = re.sub(r"\D", "", str(imei))
        if len(clean_imei) == 15:
            if validate_imei_luhn(clean_imei):
                authenticity_points += 15.0
                trust_markers.append(f"VALID_IMEI_LUHN_CHECKSUM ({clean_imei})")
            else:
                fraud_flags.append(f"INVALID_IMEI_LUHN: IMEI {clean_imei} failed mod-10 Luhn validation (counterfeit indicator)")
        else:
            trust_markers.append(f"DEVICE_SERIAL_RECORDED ({imei})")
            authenticity_points += 10.0

    # 4. Line-Item Mathematical Integrity & Reconciliation - 35 pts
    taxable_val = invoice.get("taxable_value")
    claimed_tot = invoice.get("claimed_total") or invoice.get("total_amount") or invoice.get("grand_total")
    tax_comps = invoice.get("tax_components") or []
    if taxable_val is not None and claimed_tot is not None:
        rec = reconcile_invoice_line_items(
            taxable_value=float(taxable_val),
            tax_components=tax_comps,
            discounts=float(invoice.get("discounts", 0.0)),
            shipping_fee=float(invoice.get("shipping_fee", 0.0)),
            claimed_total=float(claimed_tot),
        )
        if rec["is_reconciled"]:
            authenticity_points += 35.0
            trust_markers.append(f"MATHEMATICALLY_RECONCILED_LINE_ITEMS (Discrepancy: {rec['discrepancy']:.2f})")
        else:
            fraud_flags.append(
                f"ARITHMETIC_MISMATCH: Computed total ({rec['computed_total']:,.2f}) deviates from "
                f"claimed grand total ({rec['claimed_total']:,.2f}) by {rec['discrepancy']:,.2f}"
            )

    # 5. Harmonized Tariff Code (HSN/SAC) - 10 pts
    hsn = invoice.get("hsn_sac") or invoice.get("hsn")
    if hsn:
        clean_hsn = str(hsn).strip()
        if clean_hsn.startswith(("8517", "8471", "8528", "8504")):
            authenticity_points += 10.0
            trust_markers.append(f"VALID_HSN_CLASSIFICATION ({clean_hsn} Telecommunications/Electronics)")

    # 6. Authorized Retailer & Platform Identity - 20 pts
    seller_name = str(invoice.get("seller_name", "")).lower()
    platform = str(invoice.get("platform", "")).lower()
    known_entities = {
        "cigfil", "flipkart", "amazon", "samsung", "apple", "jb hi-fi",
        "tokopedia", "blibli", "shopee", "appario", "retailnet", "supercomnet"
    }
    if any(k in seller_name or k in platform for k in known_entities):
        authenticity_points += 20.0
        trust_markers.append(f"AUTHORIZED_RETAILER_PLATFORM ({invoice.get('seller_name') or invoice.get('platform')})")

    # 7. Price Anomaly Check vs Market - 10 pts
    price = claimed_tot or invoice.get("price") or 0.0
    mod_z = 0.0
    if price and market_prices and len(market_prices) >= 3:
        mod_z = compute_robust_z_score(float(price), market_prices)
        if mod_z < -3.5:
            fraud_flags.append(f"EXTREME_PRICE_OUTLIER: Invoice price ({price:,.2f}) is statistically anomalous (z: {mod_z:.2f})")
        else:
            authenticity_points += 10.0
            trust_markers.append(f"STATISTICALLY_NORMAL_PRICE (Modified z: {mod_z:.2f})")

    # Score calculation
    deductions = len(fraud_flags) * 25.0
    final_score = max(0.0, min(1.0, (authenticity_points - deductions) / max_points))

    is_authentic = final_score >= 0.70 and len(fraud_flags) == 0
    scam_score = 0.0 if is_authentic else min(1.0, 0.40 + (len(fraud_flags) * 0.25))

    verdict = (
        "AUTHENTIC_ORIGINAL_INVOICE"
        if is_authentic
        else "SUSPICIOUS_UNVERIFIED_INVOICE"
        if final_score >= 0.40
        else "FRAUDULENT_FABRICATED_INVOICE"
    )

    return {
        "is_authentic_invoice": is_authentic,
        "authenticity_score": round(final_score, 3),
        "scam_score": round(scam_score, 3),
        "verdict": verdict,
        "trust_markers": trust_markers,
        "fraud_flags": fraud_flags,
        "reasons": trust_markers if is_authentic else fraud_flags + trust_markers,
        "gstin_validation": validate_gstin(gstin) if gstin else None,
        "imei_luhn_valid": validate_imei_luhn(imei) if imei else None,
        "modified_z_score": round(mod_z, 2),
    }


def analyze_scam_risk(
    listing_price: float,
    market_prices: List[float],
    seller_feedback_score: Optional[float] = 98.0,  # e.g. 98.5% positive
    seller_review_count: Optional[int] = 150,
    seller_account_age_days: Optional[int] = 365,
    listing_url: Optional[str] = None,
    demands_off_platform_payment: bool = False,
    invoice_data: Optional[Dict[str, Any]] = None,
    invoice_text: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Evaluates a listing or invoice against statistical price distributions, seller/domain fraud markers,
    and statutory invoice credentials (GSTIN, IRN, IMEI Luhn, line-item reconciliation).
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
            if legit.split('.')[0] in domain and not domain.endswith(legit):
                risk_points += 20.0
                reasons.append(f"TYPOSQUATTING: Domain '{domain}' mimics authorized platform '{legit}'.")
                break

    # 5. Fine-Tuned Invoice Bill Verification (Weight: up to +/- 50 pts)
    inv_eval: Optional[Dict[str, Any]] = None
    if invoice_text and not invoice_data:
        invoice_data = parse_invoice_text(invoice_text)

    if invoice_data:
        inv_eval = audit_invoice_authenticity(invoice_data, market_prices)
        if inv_eval["is_authentic_invoice"]:
            # Authentic invoice confirmed: heavy trust bonus
            risk_points = max(0.0, risk_points - 40.0)
            reasons.append(
                f"VERIFIED_INVOICE: Original tax invoice verified ({inv_eval['verdict']}) with "
                f"{len(inv_eval['trust_markers'])} statutory trust markers."
            )
        else:
            # Invoice anomalies or counterfeit indicators detected
            risk_points += 40.0
            for flag in inv_eval["fraud_flags"]:
                reasons.append(f"INVOICE_FRAUD_FLAG: {flag}")

    scam_score = min(1.0, risk_points / max_points)
    triggers_intervention = scam_score >= 0.50

    output = {
        "listing_price": listing_price,
        "modified_z_score": round(mod_z, 2),
        "scam_score": round(scam_score, 3),
        "risk_level": "CRITICAL" if scam_score >= 0.7 else "HIGH" if scam_score >= 0.5 else "MEDIUM" if scam_score >= 0.25 else "LOW",
        "triggers_scam_intervention": triggers_intervention,
        "reasons": reasons,
        "recommended_action": "BLOCK_AND_WARN" if triggers_intervention else "PROCEED_SAFE",
    }
    if inv_eval:
        output["invoice_audit"] = inv_eval

    return output
