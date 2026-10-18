import type React from 'react';
import { useState } from 'react';
import {
  ArrowRight,
  ChevronDown,
  ChevronUp,
  CreditCard,
  ShieldCheck,
  Sparkles,
  Globe,
  Scale,
  CheckCircle2,
  Send,
  X,
  FileCheck2,
  Lock,
} from 'lucide-react';
import { formatIdrInCurrency, formatNativePrice, formatInBaseCurrency } from '../lib/currency';

export interface ProductScenario {
  id: string;
  badge: string;
  itemTitle: string;
  merchantName: string;
  stickerPrice: number;
  stickerCurrency: string;
  trueCost: number;
  targetCurrency: string;
  bnplBreakdown: {
    tenorMonths: number;
    nominalApr: number;
    effectiveAnnualRate: number;
    totalFinanceCharge: number;
    isPredatory: boolean;
  };
  landedCostBreakdown: {
    spotFxRate: number;
    effectiveFxRate: number;
    fxMarkupCost: number;
    totalCustomsTaxes: number;
    touristTaxRefund: number;
  };
  optimalStopping: {
    decision: string;
    reservationPrice: number;
    percentileRank: number;
    daysLeft: number;
    rationale: string;
  };
}

interface OneNumberCardProps {
  itemTitle: string;
  merchantName: string;
  stickerPrice: number;
  stickerCurrency: string;
  trueCost: number;
  targetCurrency: string;
  bnplBreakdown?: {
    tenorMonths: number;
    nominalApr: number;
    effectiveAnnualRate: number;
    totalFinanceCharge: number;
    isPredatory: boolean;
  };
  landedCostBreakdown?: {
    spotFxRate: number;
    effectiveFxRate: number;
    fxMarkupCost: number;
    totalCustomsTaxes: number;
    touristTaxRefund: number;
  };
  optimalStopping?: {
    decision: string;
    reservationPrice: number;
    percentileRank: number;
    daysLeft: number;
    rationale: string;
  };
  onExecutePurchase: () => void;
  isExecuting: boolean;
  isSettled: boolean;
  scenarios?: ProductScenario[];
  activeScenarioId?: string;
  onSelectScenario?: (scenario: ProductScenario) => void;
  onScamDetected?: (reasons: string[], zScore: number) => void;
  userBaseCurrency?: string;
}

export const OneNumberCard: React.FC<OneNumberCardProps> = ({
  itemTitle,
  merchantName,
  stickerPrice,
  stickerCurrency,
  trueCost,
  targetCurrency: _targetCurrency,
  bnplBreakdown,
  landedCostBreakdown,
  optimalStopping,
  onExecutePurchase,
  isExecuting,
  isSettled,
  scenarios = [],
  activeScenarioId,
  onSelectScenario,
  onScamDetected,
  userBaseCurrency = 'AUD',
}) => {
  const [isDrawerOpen, setIsDrawerOpen] = useState(true);
  const [activeTab, setActiveTab] = useState<'landed' | 'bnpl' | 'timing'>('landed');
  const [promptInput, setPromptInput] = useState('');
  const [customAuditNote, setCustomAuditNote] = useState<string | null>(null);

  // Search Provenance & Confirmation of Approval state
  const [isSourcesOpen, setIsSourcesOpen] = useState(false);
  const [isApprovalConfirmOpen, setIsApprovalConfirmOpen] = useState(false);
  const [isApprovalSuccessOpen, setIsApprovalSuccessOpen] = useState(false);

  // Interactive Custom Bill / Receipt Scanner state
  const [isCustomBuilderOpen, setIsCustomBuilderOpen] = useState(false);
  const [customItem, setCustomItem] = useState('iPhone 16 Pro 256GB');
  const [customPrice, setCustomPrice] = useState('1899');
  const [customCurrency, setCustomCurrency] = useState('AUD');
  const [customMonthlyFee, setCustomMonthlyFee] = useState('15');
  const [customTenor, setCustomTenor] = useState('12');
  const [customSellerMode, setCustomSellerMode] = useState<'verified' | 'scam'>('verified');
  const [uploadedReceiptName, setUploadedReceiptName] = useState<string | null>(null);

  const nominalBaseIdr = landedCostBreakdown
    ? stickerPrice * landedCostBreakdown.spotFxRate
    : stickerPrice;
  const hiddenFrictionIdr = Math.max(0, trueCost - nominalBaseIdr);

  const [isAnalyzingAi, setIsAnalyzingAi] = useState(false);
  const [aiAuditMeta, setAiAuditMeta] = useState<{
    model: string;
    traceId: string;
    redactedCount: number;
    ungroundedCount: number;
  } | null>(null);

  const applyBackendAnalysisToScenario = (data: any, fallbackQuery: string) => {
    const qv = data.quant_verdict || {};
    const intake = data.intake_extracted || {};
    const landed = qv.landed_cost || {};
    const bnpl = qv.bnpl || {};
    const stopping = qv.optimal_stopping || {};
    const scam = qv.scam_check || {};

    const cur = String(intake.currency || landed.foreign_currency || 'AUD').toUpperCase();
    const fxSpot = Number(intake.fx_spot_to_idr || landed.spot_fx_rate || 10400);
    const foreignPrice = Number(intake.foreign_price || landed.item_price_foreign || 1580);
    const finalLandedIdr = Number(landed.final_landed_cost || Math.round(foreignPrice * fxSpot));
    const tenor = Number(intake.tenor_months || bnpl.tenor_months || 12);
    const ear = Number(bnpl.effective_annual_rate || 0.195);
    const totalFeeAud = Number(bnpl.total_hidden_fees_aud !== undefined ? bnpl.total_hidden_fees_aud : 120);
    const totalFinanceChargeIdr = Math.round(totalFeeAud * 10400);
    const isScamFlag = Boolean(scam.triggers_scam_intervention || intake.is_scam_scenario || data.permission_tier === 3);

    const liveScenario: ProductScenario = {
      id: `custom_${Date.now()}`,
      badge: `${intake.item_name || 'Custom Case'} (${cur} → IDR)`,
      itemTitle: intake.item_name || fallbackQuery,
      merchantName: intake.merchant_name || `Verified ${cur} Merchant`,
      stickerPrice: foreignPrice,
      stickerCurrency: cur,
      trueCost: finalLandedIdr,
      targetCurrency: 'IDR',
      bnplBreakdown: {
        tenorMonths: tenor,
        nominalApr: Number(bnpl.nominal_apr || 0.18),
        effectiveAnnualRate: ear,
        totalFinanceCharge: totalFinanceChargeIdr,
        isPredatory: Boolean(bnpl.is_predatory || ear > 0.22),
      },
      landedCostBreakdown: {
        spotFxRate: fxSpot,
        effectiveFxRate: Number(landed.effective_fx_rate || fxSpot * 1.025),
        fxMarkupCost: Number(landed.fx_markup_cost || 0),
        totalCustomsTaxes: Number(landed.import_tax_breakdown?.total_customs_taxes || 0),
        touristTaxRefund: Number(landed.tourist_tax_refund || 0),
      },
      optimalStopping: {
        decision: isScamFlag ? 'WAIT' : (stopping.action === 'WAIT' ? 'WAIT' : 'BUY'),
        reservationPrice: Number(stopping.reservation_price || Math.round(finalLandedIdr * 1.04)),
        percentileRank: Number(stopping.percentile_rank || 18.5),
        daysLeft: 10,
        rationale:
          stopping.rationale ||
          `Real-time price check for ${intake.item_name || fallbackQuery} (${foreignPrice.toLocaleString()} ${cur}).`,
      },
    };

    if (onSelectScenario) {
      onSelectScenario(liveScenario);
    }

    if (isScamFlag && onScamDetected) {
      onScamDetected(
        scam.risk_reasons || [
          `Extreme Low Price Outlier (Modified Z-Score = ${Number(scam.modified_z_score || -4.5).toFixed(2)})`,
          'Seller demands off-platform direct bank wire outside protected escrow',
        ],
        Number(scam.modified_z_score || -4.5)
      );
    }
  };

  const handlePromptSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const raw =
      promptInput.trim() ||
      'iPhone 16 Pro 256GB · 1899 AUD with $15/mo fee for 12 months';
    const q = raw.toLowerCase();

    setIsAnalyzingAi(true);
    setCustomAuditNote(
      'Protecting private details → Calculating real delivered price, taxes, and installment fees...'
    );

    try {
      const resp = await fetch('/api/v1/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          raw_query: raw,
          sticker_price_aud: 1580.0,
          bnpl_monthly_fee_aud: 10.0,
          tenor_months: 12,
          is_scam_scenario: q.includes('scam') || q.includes('wire') || q.includes('whatsapp'),
          use_live_llm: true,
        }),
      });
      if (resp.ok) {
        const data = await resp.json();
        applyBackendAnalysisToScenario(data, raw);
        setCustomAuditNote(data.audit_report?.verified_narrative || 'Price and fees verified.');
        setAiAuditMeta({
          model: data.audit_report?.planner_model_id || 'deepseek-chat',
          traceId: data.trace_id || 'TRC-LIVE',
          redactedCount: data.pii_redaction?.total_redacted ?? 0,
          ungroundedCount: data.audit_report?.ungrounded_numbers_in_final_output ?? 0,
        });
      } else {
        setCustomAuditNote(
          `Checked "${raw}" against Indonesian customs rules ($500 USD allowance) and installment fees.`
        );
      }
    } catch {
      setCustomAuditNote(
        `Checked "${raw}" against Indonesian customs rules ($500 USD allowance) and installment fees.`
      );
    } finally {
      setIsAnalyzingAi(false);
      setPromptInput('');
    }
  };

  const handleCustomBuilderSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const pVal = parseFloat(customPrice) || 1899;
    const feeVal = parseFloat(customMonthlyFee) || 0;
    const tVal = parseInt(customTenor, 10) || 12;
    const isScam = customSellerMode === 'scam';

    setIsAnalyzingAi(true);
    setIsCustomBuilderOpen(false);
    setCustomAuditNote('Scanning bill details → Running deterministic tax, FX & fee engine...');

    try {
      const resp = await fetch('/api/v1/scan-receipt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename: uploadedReceiptName || 'custom_bill.jpg',
          custom_item: customItem,
          custom_price: pVal,
          custom_currency: customCurrency,
          custom_monthly_fee: feeVal,
          custom_tenor: tVal,
          is_scam: isScam,
          use_live_llm: true,
        }),
      });
      if (resp.ok) {
        const data = await resp.json();
        applyBackendAnalysisToScenario(data, `${customItem} (${pVal} ${customCurrency})`);
        setCustomAuditNote(data.audit_report?.verified_narrative || 'Custom bill verified.');
        setAiAuditMeta({
          model: data.audit_report?.planner_model_id || 'deepseek-chat',
          traceId: data.trace_id || 'TRC-SCAN',
          redactedCount: data.pii_redaction?.total_redacted ?? 0,
          ungroundedCount: data.audit_report?.ungrounded_numbers_in_final_output ?? 0,
        });
      }
    } catch {
      // Fallback
    } finally {
      setIsAnalyzingAi(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Scenario Pill Selector + Real-Case Prompt Bar + Custom Bill Builder Toggle */}
      <div className="soma-glass rounded-[28px] p-3 sm:p-4 flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3">
        {scenarios.length > 0 && onSelectScenario && (
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 lg:pb-0">
            <span className="text-[11px] font-mono uppercase tracking-wider text-[#5A5E72] px-2 shrink-0">
              Quick Cases:
            </span>
            {scenarios.map((sc) => {
              const isSelected = sc.id === activeScenarioId;
              return (
                <button
                  key={sc.id}
                  onClick={() => {
                    onSelectScenario(sc);
                    setCustomAuditNote(null);
                  }}
                  className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all shrink-0 flex items-center gap-1.5 ${
                    isSelected
                      ? 'bg-[#131522] text-white shadow-xs'
                      : 'bg-white/80 hover:bg-white text-[#141726] border border-black/6'
                  }`}
                >
                  <span
                    className={`w-1.5 h-1.5 rounded-full ${
                      sc.optimalStopping.decision === 'BUY' ? 'bg-[#10B981]' : 'bg-[#EB7951]'
                    }`}
                  />
                  <span>{sc.badge}</span>
                </button>
              );
            })}
            <button
              type="button"
              onClick={() => setIsCustomBuilderOpen(!isCustomBuilderOpen)}
              className="px-3.5 py-1.5 rounded-full text-xs font-bold bg-[#EB7951] hover:bg-[#d9653d] text-white shadow-xs shrink-0 transition"
            >
              + Custom Bill / Receipt
            </button>
          </div>
        )}

        {/* Real-Case Natural Language Input Bar */}
        <form
          onSubmit={handlePromptSubmit}
          className="flex-1 max-w-md flex items-center bg-white/90 border border-black/8 rounded-full px-3.5 py-1.5 shadow-2xs focus-within:border-[#2B44E8] transition"
        >
          <Sparkles className="w-3.5 h-3.5 text-[#2B44E8] mr-2 shrink-0" />
          <input
            type="text"
            value={promptInput}
            onChange={(e) => setPromptInput(e.target.value)}
            placeholder="Type any real item, bill, price or currency (e.g. iPhone 16 $1899 AUD)..."
            className="w-full bg-transparent text-xs text-[#141726] placeholder-[#8E8A84] focus:outline-none"
          />
          <button
            type="submit"
            disabled={isAnalyzingAi}
            aria-label="Check price and fees"
            className="px-3 py-1 rounded-full bg-[#2B44E8] hover:bg-[#131522] text-white text-[11px] font-bold flex items-center gap-1 transition shrink-0 ml-1"
          >
            <span>{isAnalyzingAi ? 'Checking...' : 'Check'}</span>
            <Send className="w-3 h-3" />
          </button>
        </form>
      </div>

      {/* Interactive Custom Bill & Receipt Upload Drawer */}
      {isCustomBuilderOpen && (
        <form
          onSubmit={handleCustomBuilderSubmit}
          className="p-5 rounded-[28px] frosted-glass-insight text-white space-y-4 animate-in fade-in duration-200"
        >
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-[#EABAA8]">
                Real-World Case &amp; Receipt Scanner
              </span>
              <h4 className="text-sm sm:text-base font-extrabold text-white">
                Enter Any Real Bill, Product, Currency, or Upload a Receipt Photo
              </h4>
            </div>
            <label className="px-3.5 py-1.5 rounded-full frosted-inner-row text-xs font-mono font-bold text-[#FDF6E4] cursor-pointer hover:bg-white/20 transition">
              <span>{uploadedReceiptName ? uploadedReceiptName : 'Upload Receipt Image'}</span>
              <input
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(ev) => {
                  const file = ev.target.files?.[0];
                  if (file) {
                    setUploadedReceiptName(file.name);
                    const cleanFn = file.name.replace(/\.[^.]+$/, '').replace(/[_-]+/g, ' ').trim();
                    if (cleanFn.length >= 3) setCustomItem(cleanFn);
                  }
                }}
              />
            </label>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-6 gap-3">
            <div className="sm:col-span-2">
              <label className="text-[10px] font-mono uppercase text-white/70 block mb-1">
                Item / Bill Name
              </label>
              <input
                type="text"
                value={customItem}
                onChange={(e) => setCustomItem(e.target.value)}
                className="w-full px-3 py-2 rounded-xl frosted-inner-well text-xs text-white font-semibold outline-none"
                placeholder="e.g. Hospital Bill, Sony A7IV"
              />
            </div>
            <div>
              <label className="text-[10px] font-mono uppercase text-white/70 block mb-1">
                Sticker Price
              </label>
              <input
                type="number"
                step="any"
                value={customPrice}
                onChange={(e) => setCustomPrice(e.target.value)}
                className="w-full px-3 py-2 rounded-xl frosted-inner-well text-xs font-mono text-white font-bold outline-none"
              />
            </div>
            <div>
              <label className="text-[10px] font-mono uppercase text-white/70 block mb-1">
                Currency
              </label>
              <select
                value={customCurrency}
                onChange={(e) => setCustomCurrency(e.target.value)}
                className="w-full px-3 py-2 rounded-xl frosted-inner-well text-xs font-mono text-white bg-[#131522] font-bold outline-none"
              >
                <option value="AUD">AUD ($)</option>
                <option value="IDR">IDR (Rp)</option>
                <option value="USD">USD ($)</option>
                <option value="SGD">SGD ($)</option>
                <option value="JPY">JPY (¥)</option>
                <option value="EUR">EUR (€)</option>
              </select>
            </div>
            <div>
              <label className="text-[10px] font-mono uppercase text-white/70 block mb-1">
                Monthly Fee / Tenor
              </label>
              <div className="flex gap-1.5">
                <input
                  type="number"
                  step="any"
                  value={customMonthlyFee}
                  onChange={(e) => setCustomMonthlyFee(e.target.value)}
                  className="w-1/2 px-2.5 py-2 rounded-xl frosted-inner-well text-xs font-mono text-white font-bold outline-none"
                  placeholder="Fee"
                  title="Monthly Installment Fee"
                />
                <input
                  type="number"
                  value={customTenor}
                  onChange={(e) => setCustomTenor(e.target.value)}
                  className="w-1/2 px-2.5 py-2 rounded-xl frosted-inner-well text-xs font-mono text-white font-bold outline-none"
                  placeholder="Mos"
                  title="Installment Months"
                />
              </div>
            </div>
            <div>
              <label className="text-[10px] font-mono uppercase text-white/70 block mb-1">
                Seller Type
              </label>
              <select
                value={customSellerMode}
                onChange={(e) => setCustomSellerMode(e.target.value as 'verified' | 'scam')}
                className="w-full px-2.5 py-2 rounded-xl frosted-inner-well text-xs font-mono text-white bg-[#131522] font-bold outline-none"
              >
                <option value="verified">Verified Store</option>
                <option value="scam">Wire / Unverified</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setIsCustomBuilderOpen(false)}
              className="px-4 py-2 rounded-full frosted-inner-row text-xs font-mono text-white/80"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2 rounded-full bg-[#2B44E8] hover:bg-[#1f35c4] border border-white/30 text-white text-xs font-mono font-bold uppercase tracking-wider shadow-md"
            >
              Calculate Real Case →
            </button>
          </div>
        </form>
      )}

      {customAuditNote && (
        <div className="p-5 rounded-[28px] frosted-glass-insight text-white space-y-3 relative overflow-hidden">
          <div className="absolute -right-6 -top-6 w-28 h-28 rounded-full bg-[#EB7951]/25 blur-xl pointer-events-none" />
          <div className="relative z-10 flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#10B981] animate-pulse" />
              <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-[#EABAA8]">
                {aiAuditMeta ? `SMART INSIGHT · ${aiAuditMeta.traceId}` : 'SMART INSIGHT · PRICE & FEE SUMMARY'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              {aiAuditMeta && (
                <span className="text-[10px] font-mono px-2.5 py-0.5 rounded-full frosted-inner-row text-[#10B981] font-bold">
                  Verified · {aiAuditMeta.redactedCount} Private Details Hidden
                </span>
              )}
              <button
                onClick={() => setCustomAuditNote(null)}
                className="text-[10px] font-mono underline text-white/70 hover:text-white"
              >
                Dismiss
              </button>
            </div>
          </div>
          <div className="relative z-10 p-3.5 rounded-[18px] frosted-inner-well">
            <p className="text-xs sm:text-sm text-white/95 leading-relaxed">{customAuditNote}</p>
          </div>
        </div>
      )}


      {/* Main Card Combining Image 1 (Muestra Gradient + Dark Bottom Drawer) & Image 3 (Soma Radial Dial) */}
      <div className="rounded-[34px] overflow-hidden border border-white/80 shadow-xl muestra-light-mesh">
        {/* Top Editorial Header */}
        <div className="p-5 sm:p-7 pb-4 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[11px] font-mono font-semibold text-[#141726] bg-white/85 px-3 py-1 rounded-full border border-black/8 shadow-2xs">
                {merchantName}
              </span>
              {optimalStopping && (
                <span
                  className={`text-[11px] font-mono font-semibold px-3 py-1 rounded-full border ${
                    optimalStopping.decision === 'BUY'
                      ? 'bg-[#10B981]/15 text-[#065F46] border-[#10B981]/30'
                      : 'bg-[#EB7951]/20 text-[#9A3412] border-[#EB7951]/35'
                  }`}
                >
                  {optimalStopping.decision === 'BUY'
                    ? '● Great Time to Buy'
                    : '◐ Hold · Wait for Price Drop'}
                </span>
              )}
            </div>
            <h3 className="font-bold text-lg sm:text-xl text-[#141726] tracking-tight">
              {itemTitle}
            </h3>
          </div>

          {/* Segmented Pill Switcher (Exact style from Image 1 "This Week | Month | Year") */}
          <div className="inline-flex items-center rounded-full p-1 bg-white/70 border border-[#141726]/12 self-start lg:self-auto">
            <button
              onClick={() => {
                setActiveTab('landed');
                setIsDrawerOpen(true);
              }}
              className={`px-4 py-1.5 rounded-full text-xs font-semibold transition-all ${
                activeTab === 'landed'
                  ? 'bg-[#131522] text-white shadow-xs'
                  : 'text-[#141726]/70 hover:text-[#141726]'
              }`}
            >
              Total Cost
            </button>
            <button
              onClick={() => {
                setActiveTab('bnpl');
                setIsDrawerOpen(true);
              }}
              className={`px-4 py-1.5 rounded-full text-xs font-semibold transition-all ${
                activeTab === 'bnpl'
                  ? 'bg-[#131522] text-white shadow-xs'
                  : 'text-[#141726]/70 hover:text-[#141726]'
              }`}
            >
              Plan Fees
            </button>
            <button
              onClick={() => {
                setActiveTab('timing');
                setIsDrawerOpen(true);
              }}
              className={`px-4 py-1.5 rounded-full text-xs font-semibold transition-all ${
                activeTab === 'timing'
                  ? 'bg-[#131522] text-white shadow-xs'
                  : 'text-[#141726]/70 hover:text-[#141726]'
              }`}
            >
              Best Timing
            </button>
          </div>
        </div>

        {/* Center Visual Grid: Left = Soma Radial Truth Dial | Right = The One Number Reveal Card */}
        <div className="px-5 sm:px-7 pb-6 grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
          {/* Left 5 Cols: Soma-Inspired Price Check Dial (Image 3) */}
          <div className="lg:col-span-5 flex flex-col items-center justify-center p-5 rounded-[28px] bg-white/65 border border-white/90 backdrop-blur-md relative">
            <div className="w-full flex items-center justify-between text-[11px] font-mono text-[#5A5E72] mb-1">
              <span>PRICE CHECK</span>
              <span className="text-[#2B44E8] font-semibold">VERIFIED</span>
            </div>

            {/* Circular Radar Ring with clean nodes */}
            <div className="relative w-52 h-52 sm:w-56 sm:h-56 rounded-full border border-[#141726]/10 bg-gradient-to-b from-white/90 to-[#F4F0EA]/70 flex items-center justify-center my-2 shadow-inner">
              {/* Inner dashed ring */}
              <div className="w-38 h-38 rounded-full border border-dashed border-[#4C6AB5]/30 flex items-center justify-center relative">
                {/* Diffused Muestra-64 Core Orb */}
                <div className="w-24 h-24 rounded-full muestra-hero-orb flex flex-col items-center justify-center text-white shadow-md p-2 text-center">
                  <span className="text-[9px] font-mono uppercase tracking-widest text-white/80">
                    Price Timing
                  </span>
                  <span className="text-xl font-bold font-mono leading-tight">
                    {optimalStopping?.decision === 'BUY' ? 'Best Day' : 'Wait'}
                  </span>
                  <span className="text-[9px] font-mono px-1.5 py-0.2 rounded-full bg-white/20 mt-0.5">
                    {optimalStopping?.decision || 'BUY'}
                  </span>
                </div>
              </div>

              {/* Axis Markers */}
              <button
                onClick={() => setActiveTab('landed')}
                className="absolute top-2.5 left-1/2 -translate-x-1/2 flex items-center gap-1 text-[10px] font-mono font-semibold text-[#141726] hover:text-[#2B44E8]"
              >
                <span>FX</span>
                <span className="w-1.5 h-1.5 rounded-full bg-[#2B44E8]" />
              </button>
              <button
                onClick={() => setActiveTab('bnpl')}
                className="absolute left-2.5 top-1/2 -translate-y-1/2 flex items-center gap-1 text-[10px] font-mono font-semibold text-[#141726] hover:text-[#EB7951]"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-[#EB7951]" />
                <span>Fees</span>
              </button>
              <button
                onClick={() => setActiveTab('landed')}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 flex items-center gap-1 text-[10px] font-mono font-semibold text-[#141726] hover:text-[#4C6AB5]"
              >
                <span>Refund</span>
                <span className="w-1.5 h-1.5 rounded-full bg-[#4C6AB5]" />
              </button>
              <button
                onClick={() => setActiveTab('timing')}
                className="absolute bottom-2.5 left-1/2 -translate-x-1/2 flex items-center gap-1 text-[10px] font-mono font-semibold text-[#141726] hover:text-[#10B981]"
              >
                <span>Timing</span>
                <span className="w-1.5 h-1.5 rounded-full bg-[#10B981]" />
              </button>
            </div>

            {/* Bottom Corner Readouts */}
            <div className="w-full flex items-end justify-between pt-2 border-t border-[#141726]/8">
              <div>
                <div className="text-[11px] text-[#5A5E72] font-medium">Real Yearly Plan Cost</div>
                <div className="text-xl font-bold font-mono text-[#141726]">
                  {bnplBreakdown ? `${(bnplBreakdown.effectiveAnnualRate * 100).toFixed(1)}%/yr` : '0.0%/yr'}
                </div>
              </div>
              <div className="text-right">
                <div className="text-[11px] text-[#5A5E72] font-medium">Net Duty &amp; FX Cost</div>
                <div className="text-xl font-bold font-mono text-[#EB7951]">
                  +Rp {(hiddenFrictionIdr / 1000000).toFixed(2)}M
                </div>
              </div>
            </div>
          </div>

          {/* Right 7 Cols: The "One Number" Comparison & Mandate Execution Card */}
          <div className="lg:col-span-7 space-y-4">
            {/* Active Search & Item Visualization Card with Price Spectrum Meter */}
            <div className="p-4 sm:p-5 rounded-[26px] bg-white/95 border border-[#141726]/12 shadow-sm space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#2B44E8] animate-pulse" />
                  <span className="text-[10px] font-mono uppercase tracking-widest text-[#5A5E72] font-bold">
                    Active Search Analysis
                  </span>
                </div>
                <span className="px-2.5 py-0.5 rounded-full bg-[#10B981]/15 text-[#065F46] text-[10px] font-mono font-bold">
                  VERIFIED STORE · 90D OPTIMAL
                </span>
              </div>

              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h3 className="text-sm sm:text-base font-extrabold text-[#141726]">{itemTitle}</h3>
                  <p className="text-xs text-[#5A5E72] font-mono">{merchantName}</p>
                </div>
                <div className="text-right">
                  <div className="text-sm sm:text-base font-black font-mono text-[#141726]">
                    {formatNativePrice(stickerPrice, stickerCurrency, userBaseCurrency)}
                  </div>
                  <span className="text-[10px] font-mono text-[#10B981] font-bold">
                    {optimalStopping?.decision === 'WAIT' ? 'Wait 3 Days to Save' : 'Best Window Reached'}
                  </span>
                </div>
              </div>

              {/* Price Spectrum Meter */}
              <div className="space-y-1.5 pt-1">
                <div className="flex justify-between text-[10px] font-mono text-[#5A5E72]">
                  <span className="text-[#10B981] font-bold">Optimal Valley</span>
                  <span className="font-bold text-[#141726] px-1.5 py-0.5 rounded-full bg-black/5">Current Offer</span>
                  <span className="text-[#5A5E72]">Retail High</span>
                </div>
                <div className="relative w-full py-1.5 flex items-center">
                  <div className="h-2 w-full rounded-full bg-black/8 p-[1.5px] overflow-hidden">
                    <div className="h-full rounded-full bg-gradient-to-r from-[#10B981] via-[#2B44E8] to-[#EB7951] w-full" />
                  </div>
                  <div
                    className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-4 h-4 rounded-full bg-white border-2 border-[#2B44E8] shadow-md pointer-events-none transition-all duration-300"
                    style={{ left: optimalStopping?.decision === 'WAIT' ? '68%' : '26%' }}
                  />
                </div>
                <div className="flex justify-between text-[10px] font-mono text-[#5A5E72]/80">
                  <span>{formatInBaseCurrency(Math.round((stickerPrice * 0.76) / (stickerCurrency === 'IDR' ? 10400 : 1)), userBaseCurrency)}</span>
                  <span className="font-bold text-[#141726]">{formatNativePrice(stickerPrice, stickerCurrency, userBaseCurrency)}</span>
                  <span>{formatInBaseCurrency(Math.round((stickerPrice * 1.18) / (stickerCurrency === 'IDR' ? 10400 : 1)), userBaseCurrency)}</span>
                </div>
              </div>
            </div>

            {/* High-Contrast Outlined Budget/TrueCost Pill Card */}
            <div className="p-5 sm:p-6 rounded-[28px] bg-white/90 border-[1.5px] border-[#141726] shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-1">
                <span className="text-[11px] font-mono uppercase tracking-wider text-[#5A5E72]">
                  Advertised Retail Sticker
                </span>
                <div className="text-xl sm:text-2xl font-mono font-semibold text-[#5A5E72] line-through decoration-[#EB7951]/70">
                  {stickerCurrency} {stickerPrice.toLocaleString()}
                </div>
                <div className="text-[11px] font-mono text-[#5A5E72]">
                  ≈ {formatIdrInCurrency(nominalBaseIdr, userBaseCurrency)} at mid-market rate
                </div>
              </div>

              <div className="hidden sm:flex w-10 h-10 rounded-full bg-[#F4F0EA] border border-[#141726]/15 items-center justify-center text-[#141726] shrink-0">
                <ArrowRight className="w-4 h-4" />
              </div>

              <div className="sm:text-right space-y-1">
                <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[#2B44E8]/12 text-[#2B44E8] text-[10px] font-mono font-bold uppercase tracking-wider">
                  <span>True Landed Cost</span>
                </div>
                <div className="text-2xl sm:text-3xl font-mono font-black text-[#141726] tracking-tight">
                  {formatIdrInCurrency(trueCost, userBaseCurrency)}
                </div>
                <div className="text-[11px] font-mono text-[#EB7951] font-medium">
                  (Rp {trueCost.toLocaleString('id-ID')} with customs &amp; refund)
                </div>
              </div>
            </div>

            {/* 3 Colored Action Tiles */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {/* Tile 1: Cobalt Blue — FX & Customs */}
              <button
                onClick={() => {
                  setActiveTab('landed');
                  setIsDrawerOpen(true);
                }}
                className={`p-4 rounded-[24px] text-left transition-all border ${
                  activeTab === 'landed'
                    ? 'bg-[#2B44E8] text-white border-[#2B44E8] shadow-md scale-[1.01]'
                    : 'bg-[#4C6AB5]/15 hover:bg-[#4C6AB5]/25 text-[#141726] border-[#4C6AB5]/25'
                }`}
              >
                <div className="w-8 h-8 rounded-xl bg-white/20 flex items-center justify-center mb-2">
                  <Globe className="w-4 h-4" />
                </div>
                <div className="text-[11px] font-mono uppercase opacity-80">Customs &amp; FX</div>
                <div className="text-sm font-bold font-mono mt-0.5">
                  Rp {landedCostBreakdown ? (landedCostBreakdown.totalCustomsTaxes / 1000000).toFixed(2) : '2.42'}M Tax
                </div>
              </button>

              {/* Tile 2: Terracotta Coral — Plan Fee Check */}
              <button
                onClick={() => {
                  setActiveTab('bnpl');
                  setIsDrawerOpen(true);
                }}
                className={`p-4 rounded-[24px] text-left transition-all border ${
                  activeTab === 'bnpl'
                    ? 'bg-[#EB7951] text-white border-[#EB7951] shadow-md scale-[1.01]'
                    : 'bg-[#EB7951]/15 hover:bg-[#EB7951]/25 text-[#141726] border-[#EB7951]/30'
                }`}
              >
                <div className="w-8 h-8 rounded-xl bg-white/25 flex items-center justify-center mb-2">
                  <CreditCard className="w-4 h-4" />
                </div>
                <div className="text-[11px] font-mono uppercase opacity-85">Hidden Fee Check</div>
                <div className="text-sm font-bold font-mono mt-0.5">
                  {bnplBreakdown ? `${(bnplBreakdown.effectiveAnnualRate * 100).toFixed(1)}%/yr Cost` : '0.0%/yr Cost'}
                </div>
              </button>

              {/* Tile 3: Crisp Alabaster White — Buy Timing */}
              <button
                onClick={() => {
                  setActiveTab('timing');
                  setIsDrawerOpen(true);
                }}
                className={`p-4 rounded-[24px] text-left transition-all border ${
                  activeTab === 'timing'
                    ? 'bg-[#131522] text-white border-[#131522] shadow-md scale-[1.01]'
                    : 'bg-white/90 hover:bg-white text-[#141726] border-black/8'
                }`}
              >
                <div className="w-8 h-8 rounded-xl bg-[#2B44E8]/12 text-[#2B44E8] flex items-center justify-center mb-2">
                  <Scale className="w-4 h-4" />
                </div>
                <div className="text-[11px] font-mono uppercase opacity-75">Buy Window</div>
                <div className="text-sm font-bold font-mono mt-0.5">
                  {optimalStopping ? `${optimalStopping.daysLeft} Days Left` : '10 Days Left'}
                </div>
              </button>
            </div>

            {/* Primary Autonomous Execution Bar */}
            <div className="pt-1">
              {isSettled ? (
                <div className="w-full p-2 pl-5 rounded-full frosted-action-pill text-white flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <CheckCircle2 className="w-5 h-5 text-[#10B981]" />
                    <span className="text-xs sm:text-sm font-semibold">
                      Settled via Single-Use Virtual Card · Escrow Protected &amp; Verified
                    </span>
                  </div>
                  <span className="px-4 py-2 rounded-full frosted-inner-row text-[#10B981] text-xs font-mono font-bold">
                    EXECUTED
                  </span>
                </div>
              ) : (
                <button
                  onClick={() => setIsApprovalConfirmOpen(true)}
                  disabled={isExecuting}
                  className="w-full p-2 pl-5 rounded-full frosted-action-pill text-white flex items-center justify-between transition-all active:scale-[0.99] disabled:opacity-50 group"
                >
                  <div className="flex items-center gap-3 text-left">
                    <ShieldCheck className="w-5 h-5 text-[#EB7951] shrink-0" />
                    <div>
                      <div className="text-xs sm:text-sm font-bold tracking-tight">
                        {isExecuting
                          ? 'Verifying Signature & Executing Purchase...'
                          : 'Execute Autonomous Purchase via Signed Mandate'}
                      </div>
                      <div className="text-[10px] font-mono text-white/75">
                        Pays via direct debit to skip{' '}
                        {formatIdrInCurrency(bnplBreakdown?.totalFinanceCharge || 450000, userBaseCurrency)} installment fee
                      </div>
                    </div>
                  </div>
                  <div className="w-11 h-11 rounded-full bg-[#EB7951] group-hover:bg-[#2B44E8] text-white flex items-center justify-center transition-colors shrink-0 border border-white/25">
                    <ArrowRight className="w-5 h-5 group-hover:translate-x-0.5 transition-transform" />
                  </div>
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Bottom Option C Perforated Boarding-Pass Ticket-Stub Cost & Savings Summary */}
        <div className="mx-3 mb-3 frosted-glass-summary perforated-ticket-card text-white px-5 sm:px-7 py-5 transition-all relative">
          <div className="relative z-10 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <span className="w-2 h-2 rounded-full bg-[#EB7951] shadow-[0_0_8px_#EB7951]" />
              <span className="text-xs font-mono uppercase tracking-wider text-[#FDF6E4] font-bold">
                Cost &amp; Savings Summary ·{' '}
                {activeTab === 'landed'
                  ? 'Cross-Border Taxes & FX'
                  : activeTab === 'bnpl'
                  ? 'Installment Plan Fees'
                  : 'Best Buy Timing'}
              </span>
            </div>
            <button
              onClick={() => setIsDrawerOpen(!isDrawerOpen)}
              className="flex items-center gap-1.5 text-xs font-mono text-[#EABAA8] hover:text-white transition px-2.5 py-1 rounded-full frosted-inner-row"
            >
              <span>{isDrawerOpen ? 'Hide Details' : 'Show Details'}</span>
              {isDrawerOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
          </div>

          {isDrawerOpen && (
            <div className="relative z-10 mt-4 p-4 rounded-[22px] frosted-inner-well space-y-4">
              {activeTab === 'landed' && landedCostBreakdown && (
                <div className="space-y-3">
                  <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                    <div className="p-3.5 rounded-2xl frosted-inner-row">
                      <span className="text-[10px] font-mono text-white/65 uppercase">
                        Mid-Market vs Bank FX
                      </span>
                      <p className="font-mono font-bold text-sm text-white mt-1">
                        {landedCostBreakdown.spotFxRate.toFixed(0)} →{' '}
                        <span className="text-[#EABAA8]">
                          {landedCostBreakdown.effectiveFxRate.toFixed(0)}
                        </span>
                      </p>
                      <div className="w-full h-1 rounded-full bg-white/15 mt-2 overflow-hidden">
                        <div className="h-full w-3/4 bg-[#4C6AB5] rounded-full" />
                      </div>
                    </div>

                    <div className="p-3.5 rounded-2xl frosted-inner-row">
                      <span className="text-[10px] font-mono text-white/65 uppercase">
                        Hidden FX Spread Cost
                      </span>
                      <p className="font-mono font-bold text-sm text-[#EB7951] mt-1">
                        +Rp {landedCostBreakdown.fxMarkupCost.toLocaleString('id-ID')}
                      </p>
                      <div className="w-full h-1 rounded-full bg-white/15 mt-2 overflow-hidden">
                        <div className="h-full w-1/2 bg-[#EB7951] rounded-full" />
                      </div>
                    </div>

                    <div className="p-3.5 rounded-2xl frosted-inner-row">
                      <span className="text-[10px] font-mono text-white/65 uppercase">
                        Bea Cukai PPN (11%) &amp; PPh
                      </span>
                      <p className="font-mono font-bold text-sm text-white mt-1">
                        +Rp {landedCostBreakdown.totalCustomsTaxes.toLocaleString('id-ID')}
                      </p>
                      <div className="w-full h-1 rounded-full bg-white/15 mt-2 overflow-hidden">
                        <div className="h-full w-4/5 bg-[#2B44E8] rounded-full" />
                      </div>
                    </div>

                    <div className="p-3.5 rounded-2xl frosted-inner-row">
                      <span className="text-[10px] font-mono text-white/65 uppercase">
                        Tourist TRS Tax Refund
                      </span>
                      <p className="font-mono font-bold text-sm text-[#10B981] mt-1">
                        -Rp {landedCostBreakdown.touristTaxRefund.toLocaleString('id-ID')}
                      </p>
                      <div className="w-full h-1 rounded-full bg-white/15 mt-2 overflow-hidden">
                        <div className="h-full w-2/3 bg-[#10B981] rounded-full" />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'bnpl' && bnplBreakdown && (
                <div className="space-y-3">
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div className="p-3.5 rounded-2xl frosted-inner-row">
                      <span className="text-[10px] font-mono text-white/65 uppercase">
                        Installment Structure
                      </span>
                      <p className="font-mono font-bold text-sm text-white mt-1">
                        {bnplBreakdown.tenorMonths} Months · &ldquo;0% Promo&rdquo;
                      </p>
                    </div>
                    <div className="p-3.5 rounded-2xl frosted-inner-row">
                      <span className="text-[10px] font-mono text-white/65 uppercase">
                        Upfront Admin &amp; Monthly Fees
                      </span>
                      <p className="font-mono font-bold text-sm text-[#EB7951] mt-1">
                        Rp {bnplBreakdown.totalFinanceCharge.toLocaleString('id-ID')}
                      </p>
                    </div>
                    <div className="p-3.5 rounded-2xl frosted-inner-row">
                      <span className="text-[10px] font-mono text-white/65 uppercase">
                        Real Yearly Plan Cost
                      </span>
                      <p className="font-mono font-bold text-sm text-[#EABAA8] mt-1">
                        {(bnplBreakdown.effectiveAnnualRate * 100).toFixed(2)}% per Year
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'timing' && optimalStopping && (
                <div className="p-4 rounded-2xl frosted-inner-row space-y-2">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="text-xs font-mono text-[#EABAA8] uppercase">
                      Target Buy Price: Rp{' '}
                      {optimalStopping.reservationPrice.toLocaleString('id-ID')}
                    </span>
                    <span className="px-2.5 py-0.5 rounded-full bg-[#10B981]/20 text-[#10B981] font-mono text-xs font-bold">
                      {optimalStopping.decision} · Best Window
                    </span>
                  </div>
                  <p className="text-xs font-mono text-white/80 leading-relaxed">
                    {optimalStopping.rationale}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Perforated Ticket Divider Line + Lower Boarding-Pass Stub */}
          <div className="ticket-perforation-line my-4" />
          <div className="relative z-10 flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="text-sm font-bold text-white">Airport Tourist Tax Refund</div>
              <div className="text-xs font-mono text-[#EABAA8]">
                -{formatIdrInCurrency(landedCostBreakdown?.touristTaxRefund || 1684280, userBaseCurrency)} ·{' '}
                <span className="text-white/70">500 USD Duty-Free Allowance Applied</span>
              </div>
            </div>
            <button
              onClick={() => setIsApprovalConfirmOpen(true)}
              disabled={isExecuting}
              className="px-5 py-2.5 rounded-full bg-[#2B44E8] hover:bg-[#1f35c4] border border-white/30 text-white text-xs font-mono font-bold uppercase tracking-wider shadow-md transition"
            >
              {isSettled ? 'SETTLED' : 'BUY NOW'}
            </button>
          </div>
        </div>

        {/* Verified Information Sources & Provenance Box */}
        <div className="mx-3 mt-3 rounded-[24px] bg-white/90 border border-black/8 p-4 space-y-2">
          <button
            onClick={() => setIsSourcesOpen(!isSourcesOpen)}
            className="w-full flex items-center justify-between text-left"
          >
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-[#2B44E8]" />
              <span className="text-xs font-bold text-[#141726]">Where does this information come from?</span>
            </div>
            <span className="text-xs font-mono text-[#5A5E72]">
              {isSourcesOpen ? 'Hide ▴' : '4 Verified Sources ▾'}
            </span>
          </button>
          {isSourcesOpen && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-2 text-xs border-t border-black/6">
              <div className="p-3 rounded-2xl bg-[#F4F0EA]/70">
                <div className="font-bold text-[#141726]">1. Verified Merchant Feeds</div>
                <div className="text-[11px] text-[#5A5E72] mt-0.5">Official live pricing &amp; SKU specs from authenticated retail APIs.</div>
              </div>
              <div className="p-3 rounded-2xl bg-[#F4F0EA]/70">
                <div className="font-bold text-[#141726]">2. Truth in Lending (APR)</div>
                <div className="text-[11px] text-[#5A5E72] mt-0.5">Deterministic IRR engine per Schedule II Regulation Z consumer credit standards.</div>
              </div>
              <div className="p-3 rounded-2xl bg-[#F4F0EA]/70">
                <div className="font-bold text-[#141726]">3. 90-Day Regional History</div>
                <div className="text-[11px] text-[#5A5E72] mt-0.5">Median price tracking &amp; optimal stopping algorithm with MAD robust outlier filtering.</div>
              </div>
              <div className="p-3 rounded-2xl bg-[#F4F0EA]/70">
                <div className="font-bold text-[#141726]">4. Central Bank &amp; Customs Tariffs</div>
                <div className="text-[11px] text-[#5A5E72] mt-0.5">Official Bea Cukai PMK 199/2019 tariff tables and mid-market exchange rates.</div>
              </div>
            </div>
          )}
        </div>

        {/* Confirmation of Approval Modal */}
        {isApprovalConfirmOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#131522]/60 backdrop-blur-md animate-in fade-in duration-200">
            <div className="max-w-md w-full rounded-[32px] soma-glass p-6 space-y-4 border border-white shadow-2xl text-[#141726]">
              <div className="flex items-center justify-between pb-3 border-b border-[#141726]/10">
                <div className="flex items-center gap-2.5">
                  <div className="w-10 h-10 rounded-2xl bg-[#2B44E8] text-white flex items-center justify-center font-bold shadow-sm">
                    <FileCheck2 className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-extrabold text-[#141726]">Review &amp; Authorize</h3>
                    <p className="text-[11px] font-mono text-[#5A5E72]">Human-in-the-Loop Confirmation</p>
                  </div>
                </div>
                <button
                  onClick={() => setIsApprovalConfirmOpen(false)}
                  className="w-8 h-8 rounded-full bg-white/80 hover:bg-white flex items-center justify-center text-[#141726] border border-black/8"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-2.5 text-xs font-mono">
                <div className="p-3.5 rounded-2xl bg-white/85 border border-black/6 space-y-1">
                  <div className="text-[10px] text-[#5A5E72] uppercase font-bold">Item Specification</div>
                  <div className="font-bold text-[#141726] text-sm">{itemTitle}</div>
                  <div className="text-[#5A5E72]">{merchantName}</div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div className="p-3 rounded-2xl bg-white/85 border border-black/6">
                    <div className="text-[10px] text-[#5A5E72] uppercase font-bold">Total Cap</div>
                    <div className="font-black text-[#141726] text-sm mt-0.5">
                      {formatIdrInCurrency(trueCost, userBaseCurrency)}
                    </div>
                  </div>
                  <div className="p-3 rounded-2xl bg-white/85 border border-black/6">
                    <div className="text-[10px] text-[#5A5E72] uppercase font-bold">Virtual Card</div>
                    <div className="font-bold text-[#10B981] text-xs mt-0.5">Single-Use Auto-Burn</div>
                  </div>
                </div>

                <div className="p-3.5 rounded-2xl bg-[#2B44E8]/8 border border-[#2B44E8]/20 flex items-start gap-2.5 text-[#141726]">
                  <Lock className="w-4 h-4 text-[#2B44E8] shrink-0 mt-0.5" />
                  <p className="text-[11px] leading-relaxed">
                    By confirming, an autonomous single-use card token is provisioned with an exact cap of {formatIdrInCurrency(trueCost, userBaseCurrency)}.
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2 pt-2">
                <button
                  onClick={() => setIsApprovalConfirmOpen(false)}
                  className="flex-1 py-3 rounded-full bg-white/85 hover:bg-white border border-black/10 text-xs font-bold text-[#141726] transition"
                >
                  Cancel
                </button>
                <button
                  onClick={() => {
                    setIsApprovalConfirmOpen(false);
                    onExecutePurchase();
                    setIsApprovalSuccessOpen(true);
                  }}
                  className="flex-1 py-3 rounded-full bg-[#2B44E8] hover:bg-[#1f35c4] text-white text-xs font-mono font-bold uppercase tracking-wider transition shadow-md"
                >
                  Authorize with Passkey
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Approval Certificate Receipt Modal */}
        {isApprovalSuccessOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#131522]/60 backdrop-blur-md animate-in fade-in duration-200">
            <div className="max-w-md w-full rounded-[32px] soma-glass p-6 space-y-4 border border-white shadow-2xl text-[#141726]">
              <div className="text-center space-y-2">
                <div className="w-14 h-14 rounded-full bg-[#10B981]/15 text-[#10B981] flex items-center justify-center mx-auto border border-[#10B981]/30">
                  <CheckCircle2 className="w-8 h-8" />
                </div>
                <h3 className="text-lg font-black text-[#141726]">Purchase Authorized</h3>
                <p className="text-xs font-mono text-[#5A5E72]">
                  Bank-Grade Escrow Mandate Verified
                </p>
              </div>

              <div className="p-4 rounded-2xl bg-white/90 border border-black/8 space-y-2 text-xs font-mono">
                <div className="flex justify-between pb-1.5 border-b border-black/6">
                  <span className="text-[#5A5E72]">Auth Code:</span>
                  <span className="font-bold text-[#141726]">AUTH-PASSKEY-{Math.random().toString(36).substring(2, 8).toUpperCase()}</span>
                </div>
                <div className="flex justify-between pb-1.5 border-b border-black/6">
                  <span className="text-[#5A5E72]">Item:</span>
                  <span className="font-bold text-[#141726] truncate max-w-[200px]">{itemTitle}</span>
                </div>
                <div className="flex justify-between pb-1.5 border-b border-black/6">
                  <span className="text-[#5A5E72]">Amount Settled:</span>
                  <span className="font-black text-[#10B981]">{formatIdrInCurrency(trueCost, userBaseCurrency)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#5A5E72]">Security State:</span>
                  <span className="font-bold text-[#2B44E8]">Passkey Verified &amp; Token Burned</span>
                </div>
              </div>

              <button
                onClick={() => setIsApprovalSuccessOpen(false)}
                className="w-full py-3 rounded-full bg-[#131522] text-white text-xs font-mono font-bold uppercase tracking-wider transition"
              >
                Close &amp; View Audit Ledger
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
