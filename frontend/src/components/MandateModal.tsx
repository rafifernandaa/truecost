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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl text-slate-100">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <KeyRound className="w-5 h-5 text-indigo-400" />
            <h2 className="font-bold text-base text-white">Create Signed Intent Mandate</h2>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-200">
            <X className="w-5 h-5" />
          </button>
        </div>

        <p className="text-xs text-slate-400 mt-3 leading-relaxed">
          Under the <strong>Google AP2 standard</strong>, the AI agent can only execute transactions inside your cryptographically pre-authorized boundaries. Your Ed25519 private key never leaves this browser.
        </p>

        {errorMsg && (
          <div className="p-3 mt-3 rounded-lg bg-red-950/60 border border-red-800/60 text-red-300 text-xs">
            {errorMsg}
          </div>
        )}

        <div className="space-y-3 mt-4 text-xs">
          <div>
            <label className="block text-slate-400 font-medium mb-1">Target Item Query</label>
            <input
              type="text"
              value={itemQuery}
              onChange={(e) => setItemQuery(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-100 text-xs focus:ring-1 focus:ring-indigo-500 outline-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-400 font-medium mb-1">Max Budget Cap (IDR)</label>
              <input
                type="number"
                value={maxBudget}
                onChange={(e) => setMaxBudget(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-100 text-xs font-mono focus:ring-1 focus:ring-indigo-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-slate-400 font-medium mb-1">Horizon (Days)</label>
              <input
                type="number"
                value={deadlineDays}
                onChange={(e) => setDeadlineDays(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-100 text-xs font-mono focus:ring-1 focus:ring-indigo-500 outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-400 font-medium mb-1">Max Acceptable APR (%)</label>
            <input
              type="number"
              step="0.01"
              value={maxApr}
              onChange={(e) => setMaxApr(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-100 text-xs font-mono focus:ring-1 focus:ring-indigo-500 outline-none"
            />
            <span className="text-[10px] text-slate-500">Agent will block financing exceeding {(maxApr * 100).toFixed(0)}% EAR.</span>
          </div>
        </div>

        <div className="flex items-center justify-end gap-2.5 mt-6 pt-3 border-t border-slate-800">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
          >
            Cancel
          </button>
          <button
            onClick={handleSignAndSubmit}
            disabled={isSubmitting}
            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-lg shadow-indigo-600/30 transition disabled:opacity-50"
          >
            <ShieldCheck className="w-4 h-4" />
            {isSubmitting ? 'Signing & Reserving...' : 'Sign Mandate (Ed25519)'}
          </button>
        </div>
      </div>
    </div>
  );
};
