from typing import Dict, Any, Optional

# Indonesian Customs (Bea Cukai) standard rates for electronics (e.g. laptops, HS 8471.30)
# - Import Duty (Bea Masuk): 0% for laptops under WTO ITA
# - PPN (Value Added Tax): 11%
# - PPh pasal 22 (Income tax import): 7.5% (with tax ID / NPWP) or 15% (without NPWP)
# - De minimis passenger allowance: FOB USD 500 per passenger (if hand-carried), or USD 3 for postal

def compute_landed_cost(
    item_price_foreign: float,
    foreign_currency: str,
    target_currency: str = "IDR",
    fx_spot_rate: float = 10400.0,  # e.g., AUD to IDR
    fx_spread_percent: float = 0.025,  # 2.5% card / bank FX markup
    shipping_and_insurance_foreign: float = 0.0,
    has_npwp: bool = True,
    is_tourist_refund_eligible: bool = False,
    tourist_tax_rate: float = 0.10,  # e.g. 10% Australian GST refund (TRS)
    is_personal_passenger: bool = True,
    passenger_de_minimis_usd: float = 500.0,
    usd_to_foreign_rate: float = 0.65  # e.g. 1 AUD = 0.65 USD
) -> Dict[str, Any]:
    """
    Computes true cross-border landed cost including FX spreads, shipping,
    duties, taxes, and tourist VAT/GST refunds.
    """
    # 1. Effective FX rate applied by consumer payment cards/remittance
    effective_fx_rate = fx_spot_rate * (1.0 + fx_spread_percent)
    fx_markup_cost_target = item_price_foreign * (effective_fx_rate - fx_spot_rate)

    # 2. Base item price in target currency
    base_item_target = item_price_foreign * effective_fx_rate
    shipping_target = shipping_and_insurance_foreign * effective_fx_rate

    # CIF = Cost + Insurance + Freight
    cif_foreign = item_price_foreign + shipping_and_insurance_foreign
    cif_usd = cif_foreign * usd_to_foreign_rate

    # 3. Customs Duty & Import Taxes (Indonesian rules for personal import)
    # If passenger carriage, deductible threshold up to USD 500
    duty_free_usd = passenger_de_minimis_usd if is_personal_passenger else 3.0
    taxable_usd = max(0.0, cif_usd - duty_free_usd)

    if cif_usd > 0:
        taxable_fraction = taxable_usd / cif_usd
    else:
        taxable_fraction = 0.0

    taxable_base_target = (cif_foreign * effective_fx_rate) * taxable_fraction

    # Import duty: 0% for laptops
    import_duty_rate = 0.0
    import_duty_target = taxable_base_target * import_duty_rate

    # PPN (VAT): 11% on (taxable base + import duty)
    ppn_rate = 0.11
    ppn_target = (taxable_base_target + import_duty_target) * ppn_rate

    # PPh 22: 7.5% with NPWP, 15% without
    pph_rate = 0.075 if has_npwp else 0.15
    pph_target = (taxable_base_target + import_duty_target) * pph_rate

    total_import_taxes_target = import_duty_target + ppn_target + pph_target

    # 4. Tourist Tax Refund (e.g. Australian TRS: 10% refund on items > AUD 300)
    refund_target = 0.0
    if is_tourist_refund_eligible and item_price_foreign >= 300.0:
        refund_target = (item_price_foreign * tourist_tax_rate) * effective_fx_rate

    # 5. Net Total Landed Cost
    net_total_landed_target = (
        base_item_target
        + shipping_target
        + total_import_taxes_target
        - refund_target
    )

    return {
        "item_price_foreign": round(item_price_foreign, 2),
        "foreign_currency": foreign_currency,
        "target_currency": target_currency,
        "spot_fx_rate": round(fx_spot_rate, 4),
        "effective_fx_rate": round(effective_fx_rate, 4),
        "fx_markup_cost": round(fx_markup_cost_target, 2),
        "shipping_cost": round(shipping_target, 2),
        "import_tax_breakdown": {
            "cif_usd_equivalent": round(cif_usd, 2),
            "duty_free_allowance_usd": round(duty_free_usd, 2),
            "taxable_base": round(taxable_base_target, 2),
            "import_duty": round(import_duty_target, 2),
            "vat_ppn": round(ppn_target, 2),
            "income_tax_pph": round(pph_target, 2),
            "total_customs_taxes": round(total_import_taxes_target, 2),
        },
        "tourist_tax_refund": round(refund_target, 2),
        "final_landed_cost": round(net_total_landed_target, 2),
        "summary": (
            f"Sticker: {item_price_foreign:,.2f} {foreign_currency} -> "
            f"Net Landed Cost: {net_total_landed_target:,.2f} {target_currency} "
            f"(incl. {total_import_taxes_target:,.2f} tax, -{refund_target:,.2f} refund)."
        )
    }
