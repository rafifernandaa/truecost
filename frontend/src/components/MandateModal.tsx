import type React from 'react';
import { useState } from 'react';
import { KeyRound, ShieldCheck, X } from 'lucide-react';
import { signIntentMandate, type UserKeyPair } from '../lib/crypto';

interface MandateModalProps {
  isOpen: boolean;
  onClose: () => void;
  keyPair: UserKeyPair;
  onMandateCreated: (mandate: any, bankResponse: any) => void;
}

export const MandateModal: React.FC<MandateModalProps> = ({
  isOpen,
  onClose,
  keyPair,
  onMandateCreated,
}) => {
  const [itemQuery, setItemQuery] = useState('Lenovo ThinkPad T14s Gen 4 (16GB RAM, 512GB SSD)');
  const [maxBudget, setMaxBudget] = useState(18500000);
  const [deadlineDays, setDeadlineDays] = useState(14);
  const [maxApr, setMaxApr] = useState(0.15);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSignAndSubmit = async () => {
    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      const now = new Date();
      const expires = new Date(now.getTime() + deadlineDays * 24 * 60 * 60 * 1000);

      const mandatePayload = {
        mandate_id: `MANDATE-${Date.now().toString(36).toUpperCase()}`,
        user_public_key: keyPair.publicKeyHex,
        item_query: itemQuery,
        max_budget: Number(maxBudget),
        currency: 'IDR',
        allowed_payment_methods: ['DEBIT', 'CASH'],
        max_acceptable_apr: Number(maxApr),
        allow_cross_border: true,
        cooling_off_seconds: 0,
        created_at: now.toISOString(),
        expires_at: expires.toISOString(),
      };

      // 1. Sign in-browser with Ed25519 private key
      const signatureHex = signIntentMandate(mandatePayload, keyPair.secretKeyHex);
      const signedMandate = {
        ...mandatePayload,
        user_signature: signatureHex,
      };

      // 2. Submit to Sandbox Bank
      const res = await fetch('/api/mandates/intent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(signedMandate),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Bank mandate registration failed.');
      }

      const bankResult = await res.json();
      onMandateCreated(signedMandate, bankResult);
      onClose();
    } catch (err: any) {
      setErrorMsg(err.message || 'Signature or bank connection error.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="max-w-md w-full bg-zinc-950 border border-zinc-800 rounded-xl p-5 sm:p-6 shadow-2xl text-zinc-100">
        <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-300">
              <KeyRound className="w-4 h-4" />
            </div>
            <div>
              <h2 className="font-semibold text-sm sm:text-base text-zinc-100">Issue Signed Intent Mandate</h2>
              <p className="text-[11px] font-mono text-zinc-500">AP2 Verifiable Pre-Authorization</p>
            </div>
          </div>
          <button onClick={onClose} className="text-zinc-500 hover:text-zinc-300">
            <X className="w-4 h-4" />
          </button>
        </div>

        <p className="text-xs text-zinc-400 font-mono mt-3 leading-relaxed">
          The AI participant executes purchases strictly within these signed bounds. Your Ed25519 private key never leaves this browser sandbox.
        </p>

        {errorMsg && (
          <div className="p-3 mt-3 rounded-lg bg-zinc-900 border border-red-900/50 text-red-400 text-xs font-mono">
            {errorMsg}
          </div>
        )}

        <div className="space-y-3 mt-4 text-xs">
          <div>
            <label className="block text-[11px] font-mono text-zinc-400 uppercase tracking-wider mb-1">
              Target Product Query
            </label>
            <input
              type="text"
              value={itemQuery}
              onChange={(e) => setItemQuery(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-zinc-900/80 border border-zinc-800 text-zinc-100 text-xs focus:border-zinc-600 focus:outline-none transition"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-mono text-zinc-400 uppercase tracking-wider mb-1">
                Max Budget Cap (IDR)
              </label>
              <input
                type="number"
                value={maxBudget}
                onChange={(e) => setMaxBudget(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-lg bg-zinc-900/80 border border-zinc-800 text-zinc-100 text-xs font-mono focus:border-zinc-600 focus:outline-none transition"
              />
            </div>

            <div>
              <label className="block text-[11px] font-mono text-zinc-400 uppercase tracking-wider mb-1">
                Horizon (Days)
              </label>
              <input
                type="number"
                value={deadlineDays}
                onChange={(e) => setDeadlineDays(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-lg bg-zinc-900/80 border border-zinc-800 text-zinc-100 text-xs font-mono focus:border-zinc-600 focus:outline-none transition"
              />
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-mono text-zinc-400 uppercase tracking-wider mb-1">
              Max Acceptable APR (%)
            </label>
            <input
              type="number"
              step="0.01"
              value={maxApr}
              onChange={(e) => setMaxApr(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-lg bg-zinc-900/80 border border-zinc-800 text-zinc-100 text-xs font-mono focus:border-zinc-600 focus:outline-none transition"
            />
            <span className="text-[10px] text-zinc-500 font-mono mt-0.5 block">
              Agent will block any financing option exceeding {(maxApr * 100).toFixed(0)}% EAR.
            </span>
          </div>
        </div>

        <div className="flex items-center justify-end gap-2.5 mt-6 pt-3 border-t border-zinc-800">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 text-xs font-medium transition"
          >
            Cancel
          </button>
          <button
            onClick={handleSignAndSubmit}
            disabled={isSubmitting}
            className="px-4 py-2 rounded-lg bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-medium flex items-center gap-1.5 transition active:scale-[0.98] disabled:opacity-50"
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            {isSubmitting ? 'Signing & Reserving...' : 'Sign Mandate (Ed25519)'}
          </button>
        </div>
      </div>
    </div>
  );
};
