import type React from 'react';
import { useState, useEffect } from 'react';
import { ShieldAlert, AlertTriangle, X, ShieldCheck } from 'lucide-react';

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
  listingPrice = 3990000,
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#131522]/65 backdrop-blur-md animate-in fade-in duration-200">
      <div className="max-w-lg w-full rounded-[32px] overflow-hidden frosted-glass-shield text-white relative">
        <div className="absolute -right-8 -top-8 w-36 h-36 rounded-full bg-[#EB7951]/30 blur-2xl pointer-events-none" />
        {/* Header */}
        <div className="relative z-10 p-6 pb-4 flex items-start justify-between gap-3 border-b border-white/15 bg-gradient-to-r from-[#EB7951]/25 via-transparent to-[#2B44E8]/20">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-2xl bg-[#EB7951] flex items-center justify-center text-white shadow-md shrink-0 border border-white/25">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-bold text-base text-white">
                  Safety Protection Hold
                </h2>
                <span className="text-[10px] font-mono uppercase px-2.5 py-0.5 rounded-full frosted-inner-row text-[#EABAA8] font-bold">
                  Suspicious Listing Alert
                </span>
              </div>
              <p className="text-xs text-white/75 font-mono mt-0.5">
                Autonomous Execution Halted · Rp {listingPrice.toLocaleString('id-ID')} Suspicious Quote
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full frosted-inner-row hover:bg-white/20 flex items-center justify-center text-white/80 hover:text-white transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="relative z-10 p-6 space-y-4">
          {/* Risk Summary Frosted Inner Well */}
          <div className="p-4 rounded-2xl frosted-inner-well text-xs space-y-2.5">
            <div className="flex items-center justify-between font-mono">
              <span className="text-white/80">Price Risk Level:</span>
              <span className="px-2.5 py-0.5 rounded-full bg-[#EB7951] text-white font-bold">
                High Risk ({Math.abs(modifiedZScore) > 3 ? '76% Below Normal' : 'Unusual Discount'})
              </span>
            </div>
            <p className="text-white/80 text-[11px] leading-relaxed font-mono">
              Verified retail listings sell near the normal market price. This listing is priced far below normal retail value and shows red flags associated with off-platform phishing or non-delivery fraud.
            </p>

            <div className="pt-2 border-t border-white/15 space-y-1.5">
              <div className="text-[10px] font-mono text-[#EABAA8] uppercase tracking-wider">
                Safety Warnings Detected:
              </div>
              {scamReasons.map((reason, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-2 text-white/95 text-[11px] font-mono p-2 rounded-xl frosted-inner-row"
                >
                  <AlertTriangle className="w-3.5 h-3.5 text-[#EB7951] shrink-0 mt-0.5" />
                  <span>{reason}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Cognitive Friction Diagnostic Questionnaire */}
          <div className="space-y-2 text-xs">
            <p className="font-semibold text-[#EABAA8] text-xs font-mono uppercase tracking-wider">
              Mandatory Human-in-the-Loop Attestation:
            </p>
            <label className="flex items-start gap-3 p-3 rounded-2xl frosted-inner-row cursor-pointer hover:bg-white/15 transition">
              <input
                type="checkbox"
                checked={q1Checked}
                onChange={(e) => setQ1Checked(e.target.checked)}
                className="mt-0.5 rounded border-white/30 bg-transparent text-[#EB7951] focus:ring-0"
              />
              <span className="text-[11px] text-white/90 leading-snug">
                I confirm I was NOT directed by an external seller on WhatsApp, Telegram, or social media to bypass platform escrow.
              </span>
            </label>
            <label className="flex items-start gap-3 p-3 rounded-2xl frosted-inner-row cursor-pointer hover:bg-white/15 transition">
              <input
                type="checkbox"
                checked={q2Checked}
                onChange={(e) => setQ2Checked(e.target.checked)}
                className="mt-0.5 rounded border-white/30 bg-transparent text-[#EB7951] focus:ring-0"
              />
              <span className="text-[11px] text-white/90 leading-snug">
                I acknowledge that this listing is 75%+ below the verified market median (Rp 17.2M) and carries severe loss risk.
              </span>
            </label>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-end gap-2.5 pt-3 border-t border-white/10">
            <button
              onClick={onClose}
              className="w-full sm:w-auto px-5 py-2.5 rounded-full bg-white hover:bg-[#FDF6E4] text-[#141726] text-xs font-bold flex items-center justify-center gap-1.5 transition active:scale-[0.98]"
            >
              <ShieldCheck className="w-4 h-4 text-[#2B44E8]" />
              Abort &amp; Protect Funds (Recommended)
            </button>
            <button
              onClick={onOverrideConfirm}
              disabled={!canOverride}
              className={`w-full sm:w-auto px-4 py-2.5 rounded-full text-xs font-mono transition ${
                canOverride
                  ? 'bg-[#EB7951] text-white hover:bg-[#d9653d]'
                  : 'bg-white/5 text-white/35 border border-white/10 cursor-not-allowed'
              }`}
            >
              {countdown > 0 ? `Cooling-Off Lock (${countdown}s)` : 'Force Override & Log Risk'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
