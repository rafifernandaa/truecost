import type React from 'react';
import { useState } from 'react';
import { ArrowRight, ChevronDown, ChevronUp, Clock, CreditCard, ShieldCheck } from 'lucide-react';

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
}

export const OneNumberCard: React.FC<OneNumberCardProps> = ({
  itemTitle,
  merchantName,
  stickerPrice,
  stickerCurrency,
  trueCost,
  targetCurrency,
  bnplBreakdown,
  landedCostBreakdown,
  optimalStopping,
  onExecutePurchase,
  isExecuting,
  isSettled,
}) => {
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'bnpl' | 'landed' | 'timing'>('bnpl');

  const diff = trueCost - stickerPrice;

  return (
    <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl overflow-hidden transition-all duration-200 hover:border-zinc-700">
      {/* Top Header */}
      <div className="p-4 sm:p-5 border-b border-zinc-800/80 bg-zinc-900/60 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] font-mono text-zinc-300 bg-zinc-800/80 px-2 py-0.5 rounded border border-zinc-700/60">
              {merchantName}
            </span>
            {optimalStopping && (
              <span className={`text-[11px] font-mono px-2 py-0.5 rounded border ${
                optimalStopping.decision === 'BUY'
                  ? 'bg-emerald-950/30 text-emerald-400 border-emerald-900/40'
                  : 'bg-zinc-800 text-zinc-400 border-zinc-700'
              }`}>
                {optimalStopping.decision === 'BUY' ? 'Optimal Buy Window' : 'Hold: Wait for Price Drop'}
              </span>
            )}
          </div>
          <h3 className="font-semibold text-sm sm:text-base text-zinc-100">{itemTitle}</h3>
        </div>

        {/* Action Button */}
        <div>
          {isSettled ? (
            <div className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-emerald-950/30 text-emerald-400 border border-emerald-900/40 text-xs font-mono">
              <ShieldCheck className="w-4 h-4" />
              Settled via Disposable Token
            </div>
          ) : (
            <button
              onClick={onExecutePurchase}
              disabled={isExecuting}
              className="w-full sm:w-auto px-4 py-2 rounded-lg bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-medium flex items-center justify-center gap-2 transition active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
            >
              {isExecuting ? (
                <>
                  <span className="w-3.5 h-3.5 border-2 border-zinc-900 border-t-transparent rounded-full animate-spin" />
                  Verifying & Executing...
                </>
              ) : (
                'Execute Purchase via Mandate'
              )}
            </button>
          )}
        </div>
      </div>

      {/* The One Number Comparison Section */}
      <div className="p-4 sm:p-6 grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6 items-center">
        {/* Left: Advertised Sticker vs Net TrueCost */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-lg bg-zinc-950/80 border border-zinc-800/80">
          <div>
            <div className="text-[11px] text-zinc-500 uppercase tracking-wider font-mono">Advertised Sticker</div>
            <div className="text-lg font-mono font-medium text-zinc-400 mt-0.5">
              {stickerCurrency} {stickerPrice.toLocaleString()}
            </div>
            <div className="text-[11px] text-zinc-600 font-mono">Nominal retail listing</div>
          </div>

          <div className="hidden sm:flex w-7 h-7 rounded-md bg-zinc-900 border border-zinc-800 items-center justify-center text-zinc-500">
            <ArrowRight className="w-3.5 h-3.5" />
          </div>

          <div>
            <div className="text-[11px] text-zinc-400 uppercase tracking-wider font-mono flex items-center gap-1.5">
              <span>The TrueCost</span>
              <span className="w-1.5 h-1.5 rounded-full bg-zinc-400" />
            </div>
            <div className="text-2xl font-mono font-bold text-white tracking-tight mt-0.5">
              {targetCurrency} {trueCost.toLocaleString('id-ID')}
            </div>
            <div className="text-[11px] text-zinc-400 font-mono">
              {diff > 0 ? `+${diff.toLocaleString()} net duties & spreads` : 'All frictions accounted'}
            </div>
          </div>
        </div>

        {/* Right: Key Quantitative Indices */}
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="p-3.5 rounded-lg bg-zinc-950/60 border border-zinc-850">
            <div className="flex items-center gap-1.5 text-zinc-400">
              <CreditCard className="w-3.5 h-3.5 text-zinc-500" />
              <span className="text-[11px] font-mono uppercase tracking-wider">Effective APR</span>
            </div>
            <div className="font-semibold font-mono text-zinc-100 text-sm mt-1">
              {bnplBreakdown ? `${(bnplBreakdown.effectiveAnnualRate * 100).toFixed(1)}% EAR` : '0.0%'}
            </div>
            <div className="text-[11px] text-zinc-500 mt-0.5 font-mono">
              {bnplBreakdown?.isPredatory ? 'Warning: Hidden charges' : 'Zero predatory fees'}
            </div>
          </div>

          <div className="p-3.5 rounded-lg bg-zinc-950/60 border border-zinc-850">
            <div className="flex items-center gap-1.5 text-zinc-400">
              <Clock className="w-3.5 h-3.5 text-zinc-500" />
              <span className="text-[11px] font-mono uppercase tracking-wider">Buy Timing</span>
            </div>
            <div className="font-semibold font-mono text-zinc-100 text-sm mt-1">
              {optimalStopping?.decision === 'BUY' ? 'Execute Now' : 'Hold / Wait'}
            </div>
            <div className="text-[11px] text-zinc-500 mt-0.5 font-mono">
              {optimalStopping ? `${optimalStopping.daysLeft}d left in horizon` : 'Within budget band'}
            </div>
          </div>
        </div>
      </div>

      {/* Expandable Mathematical & Policy Breakdown Drawer */}
      <div className="border-t border-zinc-800 bg-zinc-900/30">
        <button
          onClick={() => setIsDrawerOpen(!isDrawerOpen)}
          className="w-full py-2.5 px-4 sm:px-6 flex items-center justify-between text-xs font-medium text-zinc-400 hover:text-zinc-200 transition"
        >
          <span className="font-mono text-[11px] tracking-wider uppercase text-zinc-500">
            Audit Ledger & Quantitative Breakdown
          </span>
          <div className="flex items-center gap-1 text-zinc-300 font-mono text-[11px]">
            <span>{isDrawerOpen ? 'Hide Audit Proof' : 'Inspect Math Proof'}</span>
            {isDrawerOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </div>
        </button>

        {isDrawerOpen && (
          <div className="p-4 sm:p-6 border-t border-zinc-800 bg-zinc-950/60 space-y-4">
            {/* Drawer Tabs */}
            <div className="flex flex-wrap items-center gap-1.5 border-b border-zinc-800 pb-3 text-xs">
              <button
                onClick={() => setActiveTab('bnpl')}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
                  activeTab === 'bnpl'
                    ? 'bg-zinc-100 text-zinc-950'
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900'
                }`}
              >
                BNPL Lie Detector
              </button>
              <button
                onClick={() => setActiveTab('landed')}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
                  activeTab === 'landed'
                    ? 'bg-zinc-100 text-zinc-950'
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900'
                }`}
              >
                Cross-Border Taxes & FX
              </button>
              <button
                onClick={() => setActiveTab('timing')}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
                  activeTab === 'timing'
                    ? 'bg-zinc-100 text-zinc-950'
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900'
                }`}
              >
                Optimal Stopping Curve
              </button>
            </div>

            {/* Tab 1: BNPL Lie Detector */}
            {activeTab === 'bnpl' && bnplBreakdown && (
              <div className="space-y-3 text-xs text-zinc-300">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="p-3 rounded-lg bg-zinc-900/90 border border-zinc-800">
                    <span className="text-[11px] font-mono text-zinc-500 uppercase">Advertised Schedule</span>
                    <p className="font-medium text-zinc-200 mt-1">{bnplBreakdown.tenorMonths} Monthly Installments</p>
                  </div>
                  <div className="p-3 rounded-lg bg-zinc-900/90 border border-zinc-800">
                    <span className="text-[11px] font-mono text-zinc-500 uppercase">Hidden Finance Charge</span>
                    <p className="font-semibold text-zinc-200 mt-1 font-mono">
                      Rp {bnplBreakdown.totalFinanceCharge.toLocaleString('id-ID')}
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-zinc-900/90 border border-zinc-800">
                    <span className="text-[11px] font-mono text-zinc-500 uppercase">Effective Annual Rate</span>
                    <p className="font-semibold text-zinc-100 mt-1 font-mono">
                      {(bnplBreakdown.effectiveAnnualRate * 100).toFixed(2)}% EAR
                    </p>
                  </div>
                </div>
                <p className="text-[11px] text-zinc-400 leading-relaxed font-mono">
                  Analysis: While advertised as 0% interest, administrative fees yield a true compounded rate of {(bnplBreakdown.effectiveAnnualRate * 100).toFixed(1)}%. TrueCost Autopilot routes direct payment to save Rp {bnplBreakdown.totalFinanceCharge.toLocaleString()}.
                </p>
              </div>
            )}

            {/* Tab 2: Landed Cost Breakdown */}
            {activeTab === 'landed' && landedCostBreakdown && (
              <div className="space-y-3 text-xs text-zinc-300">
                <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                  <div className="p-3 rounded-lg bg-zinc-900/90 border border-zinc-800">
                    <span className="text-[11px] font-mono text-zinc-500 uppercase">FX Spot vs Card</span>
                    <p className="font-medium text-zinc-200 mt-1 font-mono">
                      {landedCostBreakdown.spotFxRate.toFixed(0)} → {landedCostBreakdown.effectiveFxRate.toFixed(0)}
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-zinc-900/90 border border-zinc-800">
                    <span className="text-[11px] font-mono text-zinc-500 uppercase">Bank FX Spread</span>
                    <p className="font-medium text-zinc-200 mt-1 font-mono">
                      Rp {landedCostBreakdown.fxMarkupCost.toLocaleString('id-ID')}
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-zinc-900/90 border border-zinc-800">
                    <span className="text-[11px] font-mono text-zinc-500 uppercase">Customs & PPN</span>
                    <p className="font-medium text-zinc-200 mt-1 font-mono">
                      Rp {landedCostBreakdown.totalCustomsTaxes.toLocaleString('id-ID')}
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-zinc-900/90 border border-zinc-800">
                    <span className="text-[11px] font-mono text-zinc-500 uppercase">Tourist TRS Refund</span>
                    <p className="font-semibold text-emerald-400 mt-1 font-mono">
                      -Rp {landedCostBreakdown.touristTaxRefund.toLocaleString('id-ID')}
                    </p>
                  </div>
                </div>
                <p className="text-[11px] text-zinc-400 font-mono">
                  Indonesian Bea Cukai personal de minimis allowance applied ($500 USD threshold), 0% WTO ITA duty, 11% PPN, and 7.5% PPh with NPWP registration.
                </p>
              </div>
            )}

            {/* Tab 3: Optimal Stopping Timing */}
            {activeTab === 'timing' && optimalStopping && (
              <div className="space-y-3 text-xs text-zinc-300">
                <div className="p-3 rounded-lg bg-zinc-900/90 border border-zinc-800">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono text-zinc-400 uppercase">Backward Induction Decision:</span>
                    <span className="font-semibold text-zinc-100 font-mono">
                      {optimalStopping.decision} (Percentile {optimalStopping.percentileRank}%)
                    </span>
                  </div>
                  <p className="text-[11px] text-zinc-400 mt-1.5 leading-relaxed font-mono">
                    {optimalStopping.rationale}
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
