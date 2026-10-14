import type React from 'react';
import { useState, useEffect } from 'react';
import { ShieldAlert, AlertTriangle, X } from 'lucide-react';

interface ScamInterventionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onOverrideConfirm: () => void;
  scamReasons: string[];
  modifiedZScore: number;
  listingPrice?: number;
}

export const ScamInterventionModal: React.FC<ScamInterventionModalProps> = ({
  isOpen,
  onClose,
  onOverrideConfirm,
  scamReasons,
  modifiedZScore,
  listingPrice: _listingPrice,
}) => {
  const [countdown, setCountdown] = useState(10);
  const [q1Checked, setQ1Checked] = useState(false);
  const [q2Checked, setQ2Checked] = useState(false);

  useEffect(() => {
    if (!isOpen) {
      setCountdown(10);
      setQ1Checked(false);
      setQ2Checked(false);
      return;
    }

    const timer = setInterval(() => {
      setCountdown((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);

    return () => clearInterval(timer);
  }, [isOpen]);

  if (!isOpen) return null;

  const canOverride = countdown === 0 && q1Checked && q2Checked;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="max-w-lg w-full bg-zinc-950 border border-zinc-800 rounded-xl p-5 sm:p-6 shadow-2xl text-zinc-100">
        {/* Header */}
        <div className="flex items-start justify-between gap-3 pb-3 border-b border-zinc-800">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-200">
              <ShieldAlert className="w-5 h-5 text-red-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-semibold text-sm sm:text-base text-zinc-100">Cognitive Friction Intervention</h2>
                <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-red-950/40 text-red-400 border border-red-900/50">
                  Tier 3 Guardrail
                </span>
              </div>
              <p className="text-xs text-zinc-400 font-mono mt-0.5">Execution Halted: Outlier Scam Indicator</p>
            </div>
          </div>
          <button onClick={onClose} className="text-zinc-500 hover:text-zinc-300">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Statistical Proof Box */}
        <div className="p-3.5 my-4 rounded-lg bg-zinc-900/60 border border-zinc-800 text-xs space-y-2">
          <div className="flex items-center justify-between font-mono">
            <span className="text-zinc-400">Statistical Deviation (Modified Z-Score):</span>
            <span className="text-red-400 font-bold">{modifiedZScore.toFixed(2)}</span>
          </div>
          <p className="text-zinc-400 text-[11px] leading-relaxed font-mono">
            Standard market quotes fall within ±2.0 MAD deviations. A score of{' '}
            <span className="text-zinc-200">{modifiedZScore.toFixed(2)}</span> signals an extreme low-side outlier. 98.7% of listings in this band represent advance-fee fraud or bait-and-switch listings.
          </p>

          <div className="pt-2 border-t border-zinc-800/80 space-y-1">
            <div className="text-[11px] font-mono text-zinc-300 uppercase">Risk Indicators Flagged:</div>
            {scamReasons.map((reason, idx) => (
              <div key={idx} className="flex items-start gap-1.5 text-zinc-400 text-[11px] font-mono">
                <AlertTriangle className="w-3.5 h-3.5 text-zinc-400 flex-shrink-0 mt-0.5" />
                <span>{reason}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Cognitive Friction Diagnostic Questionnaire */}
        <div className="space-y-2 mb-5 text-xs text-zinc-300">
          <p className="font-medium text-zinc-200 text-xs">Mandatory Pre-Execution Attestation:</p>
          <label className="flex items-start gap-2.5 p-2.5 rounded-lg bg-zinc-900/40 border border-zinc-800/80 cursor-pointer hover:bg-zinc-900 transition">
            <input
              type="checkbox"
              checked={q1Checked}
              onChange={(e) => setQ1Checked(e.target.checked)}
              className="mt-0.5 rounded border-zinc-700 bg-zinc-800 text-zinc-100 focus:ring-0"
            />
            <span className="text-[11px] text-zinc-300 leading-snug">
              I confirm I was NOT instructed by an external party on WhatsApp, Telegram, or social media to pay this seller.
            </span>
          </label>
          <label className="flex items-start gap-2.5 p-2.5 rounded-lg bg-zinc-900/40 border border-zinc-800/80 cursor-pointer hover:bg-zinc-900 transition">
            <input
              type="checkbox"
              checked={q2Checked}
              onChange={(e) => setQ2Checked(e.target.checked)}
              className="mt-0.5 rounded border-zinc-700 bg-zinc-800 text-zinc-100 focus:ring-0"
            />
            <span className="text-[11px] text-zinc-300 leading-snug">
              I acknowledge that this listing is 70%+ below the true market median and carries high risk of non-delivery.
            </span>
          </label>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-end gap-2.5 pt-3 border-t border-zinc-800">
          <button
            onClick={onClose}
            className="w-full sm:w-auto px-4 py-2 rounded-lg bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-medium transition active:scale-[0.98]"
          >
            Abort & Keep Money Safe (Recommended)
          </button>
          <button
            onClick={onOverrideConfirm}
            disabled={!canOverride}
            className={`w-full sm:w-auto px-4 py-2 rounded-lg text-xs font-mono transition ${
              canOverride
                ? 'bg-zinc-900 border border-red-900/60 text-red-400 hover:bg-red-950/40'
                : 'bg-zinc-900/50 text-zinc-600 border border-zinc-850 cursor-not-allowed'
            }`}
          >
            {countdown > 0 ? `Hold Friction (${countdown}s)` : 'Force Override & Proceed'}
          </button>
        </div>
      </div>
    </div>
  );
};
