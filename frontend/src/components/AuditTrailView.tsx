import type React from 'react';
import { useState } from 'react';
import {
  History,
  ShieldCheck,
  ShieldAlert,
  CreditCard,
  CheckCircle2,
  Wifi,
  Lock,
  KeyRound,
  ArrowUpRight,
} from 'lucide-react';

interface AuditTrailViewProps {
  transactions: any[];
  executedOrders?: any[];
  disposableCards: any[];
  checkingBalance?: number;
  potBalance?: number;
  userPublicKey?: string;
  onOpenMandateModal?: () => void;
}

export const AuditTrailView: React.FC<AuditTrailViewProps> = ({
  transactions,
  executedOrders: _executedOrders,
  disposableCards,
  checkingBalance = 25000000,
  potBalance = 18500000,
  userPublicKey = '8f9d2a...4e1b',
  onOpenMandateModal,
}) => {
  const [focusedCardIdx, setFocusedCardIdx] = useState<number>(0);

  const latestCard =
    disposableCards.length > 0
      ? disposableCards[disposableCards.length - 1]
      : {
          masked_pan: '4532 •••• •••• 8841',
          spending_limit: 17582248,
          currency: 'IDR',
          status: 'SINGLE-USE READY',
        };

  return (
    <div className="soma-glass rounded-[34px] p-5 sm:p-7 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-[#141726]/8">
        <div>
          <div className="flex items-center gap-2.5">
            <h3 className="text-xl sm:text-2xl font-bold tracking-tight text-[#141726]">
              My Vault{' '}
              <span className="text-[#8E8A84] font-semibold">&amp; Audit Ledger</span>
            </h3>
            <span className="text-[10px] font-mono uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-[#131522] text-white font-semibold">
              Bank-Grade Verifiable
            </span>
          </div>
          <p className="text-xs text-[#5A5E72] font-mono mt-1">
            Interactive Sandbox Bank Accounts, Disposable Token Cards &amp; Signed Mandate Stream
          </p>
        </div>

        <div className="flex items-center gap-2">
          {onOpenMandateModal && (
            <button
              onClick={onOpenMandateModal}
              className="px-4 py-2 rounded-full bg-[#2B44E8] hover:bg-[#1e35c4] text-white text-xs font-semibold flex items-center gap-1.5 transition shadow-xs"
            >
              <KeyRound className="w-3.5 h-3.5" />
              New Mandate
            </button>
          )}
          <span className="text-xs font-mono px-3 py-2 rounded-full bg-white/85 text-[#141726] border border-black/8 font-semibold">
            {transactions.length} Ledger Events
          </span>
        </div>
      </div>

      {/* Main 2-Column Layout: Left = Stacked Overlapping Wallet Cards (Image 4 & Image 1) | Right = Transaction Stream */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left 5 Cols: Interactive Overlapping Wallet Stack (Inspired by Image 4 "My Wallet") */}
        <div className="lg:col-span-5 space-y-3">
          <div className="flex items-center justify-between text-xs font-mono text-[#5A5E72] px-1">
            <span className="uppercase tracking-wider font-semibold text-[#141726]">
              Sandbox Cards (Click to Cycle)
            </span>
            <span>{focusedCardIdx + 1} / 3 Active</span>
          </div>

          <div className="relative h-60 sm:h-64 w-full select-none pt-2">
            {/* Card 0: Obsidian & Muestra-64 Mesh Primary Checking Card */}
            <div
              onClick={() => setFocusedCardIdx(0)}
              className={`absolute inset-x-0 top-2 h-52 rounded-[28px] p-5 text-white cursor-pointer spring-morph muestra-card-mesh border border-white/15 flex flex-col justify-between ${
                focusedCardIdx === 0
                  ? 'z-30 translate-x-0 translate-y-0 scale-100 shadow-2xl'
                  : focusedCardIdx === 1
                  ? 'z-10 translate-x-6 translate-y-3 scale-[0.94] opacity-80'
                  : 'z-20 translate-x-3 translate-y-1.5 scale-[0.97] opacity-90'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-full bg-white/20 backdrop-blur-xs flex items-center justify-center font-serif font-black text-xs">
                    tc
                  </div>
                  <span className="text-xs font-mono uppercase tracking-wider text-white/80">
                    Primary Checking Vault
                  </span>
                </div>
                <Wifi className="w-4 h-4 text-white/70 rotate-90" />
              </div>

              <div>
                <div className="text-[11px] font-mono text-white/65">Available Liquidity</div>
                <div className="text-2xl sm:text-3xl font-mono font-bold tracking-tight mt-0.5">
                  Rp {checkingBalance.toLocaleString('id-ID')}
                </div>
              </div>

              <div className="flex items-center justify-between text-[11px] font-mono text-white/75 pt-2 border-t border-white/15">
                <span>Passkey: {userPublicKey.slice(0, 8)}…</span>
                <span className="px-2 py-0.5 rounded-full bg-white/15 text-white text-[10px]">
                  ACC_USER_CHECKING
                </span>
              </div>
            </div>

            {/* Card 1: Terracotta Coral & Peach Sinking Pot Escrow Card */}
            <div
              onClick={() => setFocusedCardIdx(1)}
              className={`absolute inset-x-0 top-2 h-52 rounded-[28px] p-5 text-[#141726] cursor-pointer spring-morph bg-gradient-to-br from-[#EB7951] via-[#EABAA8] to-[#FDF6E4] border border-white/60 flex flex-col justify-between ${
                focusedCardIdx === 1
                  ? 'z-30 translate-x-0 translate-y-0 scale-100 shadow-2xl'
                  : focusedCardIdx === 2
                  ? 'z-10 translate-x-6 translate-y-3 scale-[0.94] opacity-80'
                  : 'z-20 translate-x-3 translate-y-1.5 scale-[0.97] opacity-90'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-full bg-[#141726] text-white flex items-center justify-center">
                    <Lock className="w-3.5 h-3.5" />
                  </div>
                  <span className="text-xs font-mono font-bold uppercase tracking-wider text-[#141726]">
                    Protected Escrow Pot
                  </span>
                </div>
                <span className="text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full bg-[#141726] text-white">
                  LOCKED FOR MANDATE
                </span>
              </div>

              <div>
                <div className="text-[11px] font-mono text-[#141726]/75">
                  Reserved Pre-Purchase Allocation
                </div>
                <div className="text-2xl sm:text-3xl font-mono font-black tracking-tight text-[#141726] mt-0.5">
                  Rp {potBalance.toLocaleString('id-ID')}
                </div>
              </div>

              <div className="flex items-center justify-between text-[11px] font-mono text-[#141726]/80 pt-2 border-t border-[#141726]/15">
                <span>Zero-Leakage Ringfence</span>
                <span className="font-bold">ACC_SINKING_POT</span>
              </div>
            </div>

            {/* Card 2: Electric Cobalt Disposable Virtual Card */}
            <div
              onClick={() => setFocusedCardIdx(2)}
              className={`absolute inset-x-0 top-2 h-52 rounded-[28px] p-5 text-white cursor-pointer spring-morph bg-gradient-to-br from-[#2B44E8] via-[#4C6AB5] to-[#131522] border border-white/25 flex flex-col justify-between ${
                focusedCardIdx === 2
                  ? 'z-30 translate-x-0 translate-y-0 scale-100 shadow-2xl'
                  : focusedCardIdx === 0
                  ? 'z-10 translate-x-6 translate-y-3 scale-[0.94] opacity-80'
                  : 'z-20 translate-x-3 translate-y-1.5 scale-[0.97] opacity-90'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CreditCard className="w-5 h-5 text-[#EABAA8]" />
                  <span className="text-xs font-mono uppercase tracking-wider text-white/90">
                    Disposable Virtual Token
                  </span>
                </div>
                <span className="px-2.5 py-0.5 rounded-full bg-white/20 text-white text-[10px] font-mono font-bold">
                  {latestCard.status}
                </span>
              </div>

              <div>
                <div className="text-lg sm:text-xl font-mono font-bold tracking-widest text-white">
                  {latestCard.masked_pan}
                </div>
                <div className="text-xs font-mono text-[#EABAA8] mt-1">
                  Exact Cap: {latestCard.currency}{' '}
                  {latestCard.spending_limit?.toLocaleString('id-ID')}
                </div>
              </div>

              <div className="flex items-center justify-between text-[11px] font-mono text-white/75 pt-2 border-t border-white/15">
                <span>Auto-destroys after 1 settlement</span>
                <span>VISA VIRTUAL</span>
              </div>
            </div>
          </div>

          {/* Quick Card Switcher Dots */}
          <div className="flex items-center justify-center gap-2 pt-1">
            {[
              { idx: 0, label: 'Checking' },
              { idx: 1, label: 'Sinking Pot' },
              { idx: 2, label: 'Virtual Card' },
            ].map((tab) => (
              <button
                key={tab.idx}
                onClick={() => setFocusedCardIdx(tab.idx)}
                className={`px-3 py-1 rounded-full text-[11px] font-mono transition ${
                  focusedCardIdx === tab.idx
                    ? 'bg-[#131522] text-white font-semibold'
                    : 'bg-white/70 text-[#5A5E72] hover:bg-white'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Right 7 Cols: Non-Repudiable Transaction Pill Stream (Inspired by Image 4 & Image 1 Right Phone) */}
        <div className="lg:col-span-7 space-y-3">
          <div className="flex items-center justify-between text-xs font-mono px-1">
            <span className="uppercase tracking-wider font-semibold text-[#141726] flex items-center gap-1.5">
              <History className="w-3.5 h-3.5 text-[#2B44E8]" />
              Immutable Ledger Stream
            </span>
            <span className="text-[#5A5E72]">Cryptographic Audit Log</span>
          </div>

          {transactions.length === 0 ? (
            <div className="p-6 rounded-[28px] bg-white/85 border border-white/90 space-y-3">
              {/* Pre-populated realistic preview row + call to action so it never looks empty/dead */}
              <div className="p-3.5 rounded-[22px] bg-[#131522] text-white flex items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-[#2B44E8]/25 text-[#EABAA8] flex items-center justify-center font-mono font-bold text-xs shrink-0">
                    SEC
                  </div>
                  <div>
                    <div className="text-xs font-bold text-white">
                      Secure Sandbox Initialized · Device Passkey Registered
                    </div>
                    <div className="text-[11px] font-mono text-white/60">
                      Ready to verify Autonomous Protection Mandates in-browser
                    </div>
                  </div>
                </div>
                <span className="text-xs font-mono font-bold text-[#10B981] shrink-0">
                  ACTIVE
                </span>
              </div>

              <div className="text-center py-3 text-xs font-mono text-[#5A5E72]">
                Sign an Intent Mandate or click &ldquo;Execute Autonomous Purchase&rdquo; above to append live cryptographic settlement events.
              </div>
            </div>
          ) : (
            <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
              {transactions
                .slice()
                .reverse()
                .map((tx, idx) => {
                  const isSettlement = tx.type === 'PURCHASE_SETTLEMENT';
                  const isReserve = tx.type === 'RESERVE_SINKING_POT';
                  const isRejected = tx.status === 'REJECTED_BY_BANK_POLICY';

                  return (
                    <div
                      key={idx}
                      className={`p-3.5 rounded-[24px] border flex items-center justify-between gap-3 transition shadow-2xs ${
                        isRejected
                          ? 'bg-[#131522] border-[#EB7951]/50 text-white'
                          : isSettlement
                          ? 'bg-[#131522] border-white/10 text-white'
                          : 'bg-white/90 border-black/6 text-[#141726]'
                      }`}
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div
                          className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${
                            isRejected
                              ? 'bg-[#EB7951]/20 text-[#EB7951]'
                              : isSettlement
                              ? 'bg-[#2B44E8] text-white'
                              : 'bg-[#EB7951]/15 text-[#EB7951]'
                          }`}
                        >
                          {isRejected ? (
                            <ShieldAlert className="w-4.5 h-4.5" />
                          ) : isSettlement ? (
                            <CheckCircle2 className="w-4.5 h-4.5" />
                          ) : (
                            <ShieldCheck className="w-4.5 h-4.5" />
                          )}
                        </div>
                        <div className="min-w-0">
                          <div className="text-xs sm:text-sm font-bold truncate">
                            {isSettlement
                              ? 'Autonomous Cart Mandate Settled'
                              : isReserve
                              ? 'Sinking Pot Escrow Allocation'
                              : tx.type}
                          </div>
                          <div
                            className={`text-[11px] font-mono truncate mt-0.5 ${
                              isSettlement || isRejected ? 'text-white/65' : 'text-[#5A5E72]'
                            }`}
                          >
                            {tx.reason ||
                              (tx.amount
                                ? `Verified Amount: Rp ${tx.amount.toLocaleString('id-ID')}`
                                : 'Cryptographic check passed')}
                          </div>
                        </div>
                      </div>

                      <div className="text-right shrink-0">
                        {tx.amount && (
                          <div
                            className={`text-xs sm:text-sm font-mono font-bold ${
                              isRejected
                                ? 'text-[#EB7951]'
                                : isSettlement
                                ? 'text-[#EABAA8]'
                                : 'text-[#141726]'
                            }`}
                          >
                            -Rp {(tx.amount / 1000000).toFixed(2)}M
                          </div>
                        )}
                        <div
                          className={`text-[10px] font-mono flex items-center justify-end gap-0.5 ${
                            isSettlement || isRejected ? 'text-white/50' : 'text-[#5A5E72]'
                          }`}
                        >
                          <span>{new Date(tx.timestamp).toLocaleTimeString()}</span>
                          <ArrowUpRight className="w-3 h-3" />
                        </div>
                      </div>
                    </div>
                  );
                })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
