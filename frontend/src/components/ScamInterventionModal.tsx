import { useState, useEffect } from 'react';
import { AlertTriangle, ShieldAlert, CheckCircle2, XCircle } from 'lucide-react';

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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="max-w-lg w-full bg-slate-900 border-2 border-red-500/60 rounded-2xl p-6 shadow-2xl shadow-red-500/20 text-slate-100">
        {/* Header */}
        <div className="flex items-center gap-3.5 mb-4 text-red-400">
          <div className="w-12 h-12 rounded-xl bg-red-500/20 border border-red-500/30 flex items-center justify-center flex-shrink-0">
            <ShieldAlert className="w-7 h-7 text-red-400 animate-pulse" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">Revolut-Style Scam Intervention Flow</h2>
            <p className="text-xs text-red-300">Payment Halted: Extreme Anomaly Detected</p>
          </div>
        </div>

        {/* Statistical Proof Box */}
        <div className="p-3.5 rounded-xl bg-red-950/40 border border-red-800/40 mb-4 text-xs space-y-2">
          <div className="flex items-center justify-between font-semibold">
            <span className="text-slate-300">Statistical Deviation (Modified Z-score):</span>
            <span className="text-red-400 font-mono text-sm">{modifiedZScore.toFixed(2)}</span>
          </div>
          <p className="text-slate-400 text-[11px] leading-relaxed">
            Normal retail electronics vary within ±2.0 standard MAD deviations. A score of{' '}
            <strong className="text-red-300">{modifiedZScore.toFixed(2)}</strong> indicates an extreme 
            low-side anomaly. 98.7% of listings in this band represent advance-fee or bait-and-switch fraud.
          </p>
          <div className="pt-1.5 border-t border-red-900/40 space-y-1">
            <div className="font-medium text-red-300">Flagged Risk Indicators:</div>
            {scamReasons.map((reason, idx) => (
              <div key={idx} className="flex items-start gap-1.5 text-slate-300 text-[11px]">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400 flex-shrink-0 mt-0.5" />
                <span>{reason}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Cognitive Friction Diagnostic Questionnaire */}
        <div className="space-y-2.5 mb-5 text-xs text-slate-300">
          <p className="font-semibold text-slate-200">Mandatory Verification Questions:</p>
          <label className="flex items-start gap-2.5 p-2.5 rounded-lg bg-slate-800/60 border border-slate-700/60 cursor-pointer hover:bg-slate-800">
            <input
              type="checkbox"
              checked={q1Checked}
              onChange={(e) => setQ1Checked(e.target.checked)}
              className="mt-0.5 rounded border-slate-700 text-indigo-500 focus:ring-0"
            />
            <span>I confirm I was NOT instructed by someone on WhatsApp, Telegram, or social media to pay this seller.</span>
          </label>
          <label className="flex items-start gap-2.5 p-2.5 rounded-lg bg-slate-800/60 border border-slate-700/60 cursor-pointer hover:bg-slate-800">
            <input
              type="checkbox"
              checked={q2Checked}
              onChange={(e) => setQ2Checked(e.target.checked)}
              className="mt-0.5 rounded border-slate-700 text-indigo-500 focus:ring-0"
            />
            <span>I understand that this listing is 70%+ below true market median and carries high risk of non-delivery.</span>
          </label>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-end gap-3 pt-2 border-t border-slate-800">
          <button
            onClick={onClose}
            className="w-full sm:w-auto px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center justify-center gap-1.5 transition"
          >
            <XCircle className="w-4 h-4 text-slate-400" />
            Abort & Keep Money Safe (Recommended)
          </button>
          <button
            onClick={onOverrideConfirm}
            disabled={!canOverride}
            className={`w-full sm:w-auto px-4 py-2.5 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition ${
              canOverride
                ? 'bg-red-600 hover:bg-red-500 text-white shadow-lg shadow-red-600/30'
                : 'bg-slate-800/50 text-slate-500 cursor-not-allowed border border-slate-800'
            }`}
          >
            <CheckCircle2 className="w-4 h-4" />
            {countdown > 0 ? `Reflect (${countdown}s)` : 'Force Override & Proceed'}
          </button>
        </div>
      </div>
    </div>
  );
};
