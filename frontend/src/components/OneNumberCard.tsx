import { useState } from 'react';
import { ArrowRight, ChevronDown, ChevronUp, Clock, CreditCard, Sparkles, ShieldCheck } from 'lucide-react';


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
    <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl transition-all duration-300 hover:border-slate-700/80">
      {/* Top Header */}
      <div className="p-5 border-b border-slate-800/80 bg-slate-900/40 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-indigo-400 bg-indigo-500/10 px-2.5 py-0.5 rounded-full border border-indigo-500/20">
              {merchantName}
            </span>
            {optimalStopping && (
              <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                optimalStopping.decision === 'BUY'
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                  : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
              }`}>
                {optimalStopping.decision === 'BUY' ? 'Optimal Buy Window' : 'Advise: Wait for Dip'}
              </span>
            )}
          </div>
          <h3 className="font-bold text-base text-white mt-1.5">{itemTitle}</h3>
        </div>

        {/* Execution Status Button */}
        <div>
          {isSettled ? (
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-semibold">
              <ShieldCheck className="w-4 h-4" />
              Settled via Disposable Token
            </div>
          ) : (
            <button
              onClick={onExecutePurchase}
              disabled={isExecuting}
              className="w-full sm:w-auto px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 text-white text-xs font-semibold flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/30 transition"
            >
              <Sparkles className="w-4 h-4 text-indigo-200" />
              {isExecuting ? 'Verifying & Executing...' : 'Execute Buy via Mandate'}
            </button>
          )}
        </div>
      </div>

      {/* The One Number Reveal Section */}
      <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
        {/* Left: Sticker vs TrueCost */}
        <div className="flex items-center justify-between sm:justify-start gap-4 p-4 rounded-xl bg-slate-800/40 border border-slate-700/40">
          <div>
            <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Advertised Sticker</div>
            <div className="text-xl font-bold font-mono text-slate-300 mt-1">
              {stickerCurrency} {stickerPrice.toLocaleString()}
            </div>
            <div className="text-[11px] text-slate-500">Nominal store listing</div>
          </div>

          <div className="w-8 h-8 rounded-full bg-slate-700/60 flex items-center justify-center text-slate-400">
            <ArrowRight className="w-4 h-4" />
          </div>

          <div>
            <div className="text-xs text-emerald-400 uppercase tracking-wider font-semibold flex items-center gap-1">
              TrueCost (Net)
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
            </div>
            <div className="text-2xl font-black font-mono text-white mt-0.5">
              {targetCurrency} {trueCost.toLocaleString('id-ID')}
            </div>
            <div className="text-[11px] text-slate-400">
              {diff > 0 ? `+${diff.toLocaleString()} hidden friction` : 'Full true cost accounted'}
            </div>
          </div>
        </div>

        {/* Right: Quick Highlights */}
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="p-3 rounded-xl bg-slate-800/30 border border-slate-700/30">
            <div className="flex items-center gap-1.5 text-slate-400">
              <CreditCard className="w-3.5 h-3.5 text-indigo-400" />
              <span>Effective APR:</span>
            </div>
            <div className="font-bold font-mono text-white text-sm mt-1">
              {bnplBreakdown ? `${(bnplBreakdown.effectiveAnnualRate * 100).toFixed(1)}%` : '0.0%'}
            </div>
            <div className="text-[10px] text-slate-400 mt-0.5">
              {bnplBreakdown?.isPredatory ? '⚠️ Hidden Surcharges' : 'Verified Fair'}
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-800/30 border border-slate-700/30">
            <div className="flex items-center gap-1.5 text-slate-400">
              <Clock className="w-3.5 h-3.5 text-amber-400" />
              <span>Optimal Timing:</span>
            </div>
            <div className="font-bold font-mono text-white text-sm mt-1">
              {optimalStopping?.decision === 'BUY' ? 'Strong Buy' : 'Hold / Wait'}
            </div>
            <div className="text-[10px] text-slate-400 mt-0.5">
              {optimalStopping ? `${optimalStopping.daysLeft} days left in mandate` : 'In target band'}
            </div>
          </div>
        </div>
      </div>

      {/* Expandable Mathematical Evidence Drawer */}
      <div className="border-t border-slate-800/80 bg-slate-900/60">
        <button
          onClick={() => setIsDrawerOpen(!isDrawerOpen)}
          className="w-full py-2.5 px-6 flex items-center justify-between text-xs font-semibold text-slate-400 hover:text-white transition"
        >
          <span>Mathematical & Policy Audit Evidence</span>
          <div className="flex items-center gap-1 text-indigo-400">
            <span>{isDrawerOpen ? 'Collapse Details' : 'Inspect Quant Breakdown'}</span>
            {isDrawerOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </div>
        </button>

        {isDrawerOpen && (
          <div className="p-6 border-t border-slate-800/60 bg-slate-950/40">
            {/* Drawer Tabs */}
            <div className="flex items-center gap-2 mb-4 border-b border-slate-800 pb-2 text-xs">
              <button
                onClick={() => setActiveTab('bnpl')}
                className={`px-3 py-1.5 rounded-lg font-medium transition ${
                  activeTab === 'bnpl' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                BNPL Lie Detector
              </button>
              <button
                onClick={() => setActiveTab('landed')}
                className={`px-3 py-1.5 rounded-lg font-medium transition ${
                  activeTab === 'landed' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Cross-Border Taxes & FX
              </button>
              <button
                onClick={() => setActiveTab('timing')}
                className={`px-3 py-1.5 rounded-lg font-medium transition ${
                  activeTab === 'timing' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Optimal Stopping Curve
              </button>
            </div>

            {/* Tab 1: BNPL Lie Detector */}
            {activeTab === 'bnpl' && bnplBreakdown && (
              <div className="space-y-3 text-xs text-slate-300">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="text-slate-400">Advertised Plan:</span>
                    <p className="font-semibold text-white mt-0.5">{bnplBreakdown.tenorMonths} Monthly Installments</p>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="text-slate-400">Hidden Finance Charge:</span>
                    <p className="font-semibold text-amber-400 mt-0.5 font-mono">
                      Rp {bnplBreakdown.totalFinanceCharge.toLocaleString('id-ID')}
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="text-slate-400">Effective Annual Rate (EAR):</span>
                    <p className="font-semibold text-red-400 mt-0.5 font-mono">
                      {(bnplBreakdown.effectiveAnnualRate * 100).toFixed(2)}% APR
                    </p>
                  </div>
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  💡 <strong>Audit Engine Rationale:</strong> While promoted as 0% interest, upfront administrative charges and monthly service add-ons yield a compounded annual rate of {(bnplBreakdown.effectiveAnnualRate * 100).toFixed(1)}%. TrueCost routes direct debit to save Rp {bnplBreakdown.totalFinanceCharge.toLocaleString()}.
                </p>
              </div>
            )}

            {/* Tab 2: Landed Cost Breakdown */}
            {activeTab === 'landed' && landedCostBreakdown && (
              <div className="space-y-3 text-xs text-slate-300">
                <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                  <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="text-slate-400">Spot FX vs Effective:</span>
                    <p className="font-semibold text-white mt-0.5 font-mono">
                      {landedCostBreakdown.spotFxRate.toFixed(0)} → {landedCostBreakdown.effectiveFxRate.toFixed(0)}
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="text-slate-400">Card FX Spread Cost:</span>
                    <p className="font-semibold text-amber-400 mt-0.5 font-mono">
                      Rp {landedCostBreakdown.fxMarkupCost.toLocaleString('id-ID')}
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="text-slate-400">Customs Import Taxes:</span>
                    <p className="font-semibold text-white mt-0.5 font-mono">
                      Rp {landedCostBreakdown.totalCustomsTaxes.toLocaleString('id-ID')}
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="text-slate-400">Tourist TRS Refund:</span>
                    <p className="font-semibold text-emerald-400 mt-0.5 font-mono">
                      -Rp {landedCostBreakdown.touristTaxRefund.toLocaleString('id-ID')}
                    </p>
                  </div>
                </div>
                <p className="text-[11px] text-slate-400">
                  Customs calculated under Indonesian Bea Cukai passenger de minimis allowance ($500 USD), with 0% WTO ITA duty, 11% PPN, and 7.5% PPh with NPWP tax identity.
                </p>
              </div>
            )}

            {/* Tab 3: Optimal Stopping Timing */}
            {activeTab === 'timing' && optimalStopping && (
              <div className="space-y-3 text-xs text-slate-300">
                <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Decision Engine:</span>
                    <span className="font-bold text-white font-mono">
                      {optimalStopping.decision} (Percentile {optimalStopping.percentileRank}%)
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
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
