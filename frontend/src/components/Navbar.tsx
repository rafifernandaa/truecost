import { ShieldCheck, Wallet, KeyRound, Sparkles } from 'lucide-react';


interface NavbarProps {
  checkingBalance: number;
  potBalance: number;
  userPublicKey: string;
}

export const Navbar: React.FC<NavbarProps> = ({ checkingBalance, potBalance, userPublicKey }) => {
  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-40 px-4 lg:px-8 py-3.5">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        {/* Brand & Track Badge */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-emerald-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <ShieldCheck className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-bold text-lg text-white tracking-tight">TrueCost Autopilot</h1>
              <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                AI Participant
              </span>
            </div>
            <p className="text-xs text-slate-400">FinTechathon 2026 · Topic A Personal Finance</p>
          </div>
        </div>

        {/* Bank & Cryptographic State Badges */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Keypair Credential Badge */}
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60 text-xs text-slate-300">
            <KeyRound className="w-3.5 h-3.5 text-indigo-400" />
            <span className="text-slate-400 font-mono">Ed25519:</span>
            <span className="font-mono text-indigo-300 font-medium">
              {userPublicKey.slice(0, 6)}...{userPublicKey.slice(-4)}
            </span>
          </div>

          {/* Sinking Pot Vault */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300">
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <span>Sinking Pot:</span>
            <span className="font-bold font-mono">
              Rp {potBalance.toLocaleString('id-ID')}
            </span>
          </div>

          {/* Checking Account Balance */}
          <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-xs text-white shadow-sm">
            <Wallet className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-slate-300">Checking:</span>
            <span className="font-bold font-mono text-emerald-400">
              Rp {checkingBalance.toLocaleString('id-ID')}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
