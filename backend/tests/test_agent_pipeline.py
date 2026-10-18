from app.agents.pipeline import (
    redact_pii_text,
    verify_numeric_grounding,
    parse_real_user_query,
    run_full_agent_pipeline,
)


def test_redact_pii_text_masks_pan_nik_and_email():
    sample = "Buyer card 4532-1122-3344-5566 and NIK 3171021508990001 email student@unimelb.edu.au"
    res = redact_pii_text(sample)
    assert "[REDACTED_PAN]" in res["redacted_text"]
    assert "[REDACTED_NIK]" in res["redacted_text"]
    assert "[REDACTED_EMAIL]" in res["redacted_text"]
    assert "4532-1122-3344-5566" not in res["redacted_text"]
    assert res["total_redacted"] >= 3


def test_audit_agent_catches_hallucinated_numbers():
    allowed = [1580.0, 17582248.8, 0.184]
    fallback = "Verified APR is 18.4% and landed cost is IDR 17,582,249."
    # Fabricated 4.2% APR should be caught and replaced by fallback template
    bad_narrative = "This laptop has a tiny APR of 4.2% and costs IDR 9,123,456."
    audit = verify_numeric_grounding(
        narrative=bad_narrative,
        allowed_numbers=allowed,
        fallback_template=fallback,
    )
    assert audit["passed_initial_check"] is False
    assert len(audit["hallucinated_tokens_caught"]) >= 1
    assert audit["verified_narrative"] == fallback
    assert audit["ungrounded_numbers_in_final_output"] == 0


def test_run_full_agent_pipeline_end_to_end():
    res = run_full_agent_pipeline(
        raw_query="Lenovo ThinkPad T14s card 4532-8888-9999-0000",
        sticker_price_aud=1580.0,
    )
    assert res["trace_id"].startswith("TRC-")
    assert "[REDACTED_PAN]" in res["pii_redaction"]["redacted_text"]
    assert res["audit_report"]["ungrounded_numbers_in_final_output"] == 0
    assert len(res["trajectory"]) == 5
    agent_names = [step["agent_name"] for step in res["trajectory"]]
    assert agent_names == ["CaptureAgent", "MarketAgent", "QuantEngine", "PlannerAgent", "AuditAgent"]


def test_parse_real_user_query_multi_currency_and_scam():
    # Case 1: Custom AUD with monthly fee and tenor
    parsed_aud = parse_real_user_query("iPhone 16 Pro $1,899 AUD with $15/mo fee for 12m")
    assert parsed_aud["currency"] == "AUD"
    assert parsed_aud["foreign_price"] == 1899.0
    assert parsed_aud["sticker_price_aud"] == 1899.0
    assert parsed_aud["bnpl_monthly_fee_aud"] == 15.0
    assert parsed_aud["tenor_months"] == 12
    assert parsed_aud["is_scam_scenario"] is False

    # Case 2: IDR bill
    parsed_idr = parse_real_user_query("Hospital Bill Rp 8,320,000")
    assert parsed_idr["currency"] == "IDR"
    assert parsed_idr["sticker_price_idr"] == 8320000.0
    assert parsed_idr["sticker_price_aud"] == 800.0

    # Case 3: Scam / off-platform wire transfer
    parsed_scam = parse_real_user_query("Used MacBook Pro M3 $450 AUD via WhatsApp wire transfer only")
    assert parsed_scam["is_scam_scenario"] is True
    res_scam = run_full_agent_pipeline(
        raw_query="Used MacBook Pro M3 $450 AUD via WhatsApp wire transfer only"
    )
    assert res_scam["permission_tier"] == 3
    assert res_scam["quant_verdict"]["scam_check"]["risk_level"] in ("HIGH", "CRITICAL")


def test_dynamic_product_pricing_samsung_a57_without_placeholders():
    # Test 1: User in Jakarta searching for Samsung A57 with no price in query
    res_idr = run_full_agent_pipeline(
        raw_query="Samsung A57",
        user_currency="IDR",
        user_location="Jakarta",
        use_live_llm=False,  # deterministic catalog test
    )
    intake = res_idr["intake_extracted"]
    landed = res_idr["quant_verdict"]["landed_cost"]

    assert "Samsung" in intake["item_name"]
    assert intake["currency"] == "IDR"
    assert intake["foreign_price"] == 5999000.0  # Real phone price, NOT 1580!
    assert intake["foreign_price"] != 1580.0
    assert landed["final_landed_cost"] == 5999000.0
    assert landed["tourist_tax_refund"] == 0.0  # Domestic: no Australian TRS
    assert landed["import_tax_breakdown"]["total_customs_taxes"] == 0.0  # Domestic: no Bea Cukai

    # Test 2: User in Sydney searching for Samsung A57 with AUD
    res_aud = run_full_agent_pipeline(
        raw_query="Samsung A57",
        user_currency="AUD",
        user_location="Sydney",
        use_live_llm=False,
    )
    assert res_aud["intake_extracted"]["currency"] == "AUD"
    assert res_aud["intake_extracted"]["foreign_price"] == 549.0  # Real AUD price, NOT 1580!





