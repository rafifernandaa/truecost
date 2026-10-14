import type React from 'react';
import { ShieldCheck, Wallet, KeyRound, Lock } from 'lucide-react';

interface NavbarProps {
  checkingBalance: number;
  potBalance: number;
  userPublicKey: string;
}

export const Navbar: React.FC<NavbarProps> = ({ checkingBalance, potBalance, userPublicKey }) => {
  return (
    <header className="border-b border-zinc-800/80 bg-zinc-950/90 backdrop-blur-md sticky top-0 z-40 px-4 sm:px-6 lg:px-8 py-3">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        {/* Brand & Track Info */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-zinc-900 border border-zinc-700/80 flex items-center justify-center text-zinc-100 shadow-sm">
            <ShieldCheck className="w-4 h-4 text-zinc-200" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-sm tracking-tight text-white">TrueCost Autopilot</span>
              <span className="text-[10px] font-mono tracking-wider uppercase px-1.5 py-0.5 rounded bg-zinc-900 text-zinc-400 border border-zinc-800">
                AP2 Mandate
              </span>
            </div>
            <p className="text-[11px] text-zinc-500 font-mono">Autonomous Pre-Purchase Participant · Topic A</p>
          </div>
        </div>

        {/* Cryptographic & Bank Ledger Status */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Keypair Credential Badge */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-zinc-900/90 border border-zinc-800 text-[11px] text-zinc-300">
            <KeyRound className="w-3.5 h-3.5 text-zinc-400" />
            <span className="text-zinc-500 font-mono">Ed25519:</span>
            <span className="font-mono text-zinc-200">
              {userPublicKey.slice(0, 6)}...{userPublicKey.slice(-4)}
            </span>
          </div>

          {/* Sinking Pot Vault */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-zinc-900/90 border border-zinc-800 text-[11px] text-zinc-300">
            <Lock className="w-3 h-3 text-zinc-400" />
            <span className="text-zinc-500">Reserved Pot:</span>
            <span className="font-mono text-zinc-100 font-medium">
              Rp {potBalance.toLocaleString('id-ID')}
            </span>
          </div>

          {/* Checking Account Balance */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-zinc-900 border border-zinc-700/80 text-[11px] text-white">
            <Wallet className="w-3.5 h-3.5 text-zinc-300" />
            <span className="text-zinc-400">Checking:</span>
            <span className="font-mono font-semibold text-zinc-100">
              Rp {checkingBalance.toLocaleString('id-ID')}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
