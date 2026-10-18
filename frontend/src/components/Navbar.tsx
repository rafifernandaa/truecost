import type React from 'react';
import { ShieldCheck, KeyRound, Lock, Wallet, Sparkles, Smartphone, Settings, MapPin } from 'lucide-react';
import type { AgentAutonomyTier } from './MorphingBottomDock';
import { formatIdrInCurrency } from '../lib/currency';
import { LOCATION_HUBS } from '../lib/location';

interface NavbarProps {
  checkingBalance: number;
  potBalance: number;
  userPublicKey: string;
  autonomyTier?: AgentAutonomyTier;
  onOpenMandateModal?: () => void;
  onOpenSettings?: () => void;
  userBaseCurrency?: string;
  onCurrencyChange?: (curr: string) => void;
  userLocation?: string;
  onOpenLocationModal?: () => void;
  isFreshUser?: boolean;
  onToggleFreshUser?: () => void;
}

const TIER_BADGES: Record<AgentAutonomyTier, { text: string; dot: string }> = {
  tier2_online: { text: 'Auto-Buy Mode', dot: 'bg-[#10B981]' },
  tier1_idle: { text: 'Hold Mode', dot: 'bg-[#F59E0B]' },
  tier3_dnd: { text: 'Ask First', dot: 'bg-[#EB7951]' },
  tier0_invisible: { text: 'Check Only', dot: 'bg-[#94A3B8]' },
};

export const Navbar: React.FC<NavbarProps> = ({
  checkingBalance,
  potBalance,
  userPublicKey,
  autonomyTier = 'tier2_online',
  onOpenMandateModal,
  onOpenSettings,
  userBaseCurrency = 'AUD',
  onCurrencyChange,
  userLocation = 'tokyo',
  onOpenLocationModal,
  isFreshUser = false,
  onToggleFreshUser,
}) => {
  const badge = TIER_BADGES[autonomyTier];
  const activeHub = LOCATION_HUBS[userLocation] || LOCATION_HUBS.tokyo;

  return (
    <header className="sticky top-0 z-30 px-4 sm:px-6 lg:px-8 pt-3 pb-2">
      <div className="max-w-7xl mx-auto soma-glass rounded-[28px] px-4 sm:px-6 py-3 flex flex-col md:flex-row md:items-center justify-between gap-3">
        {/* Left: Editorial Brand & Protection Mode Pill */}
        <div className="flex items-center justify-between md:justify-start gap-3.5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl muestra-hero-orb flex items-center justify-center text-white shadow-sm border border-white/50">
              <ShieldCheck className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-base tracking-tight text-[#141726]">
                  TrueCost
                </span>
                <span className="font-semibold text-base tracking-tight text-[#8E8A84]">
                  Home
                </span>
                <span className="inline-flex items-center gap-1.5 text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full bg-[#131522] text-white whitespace-nowrap">
                  <span className={`w-1.5 h-1.5 rounded-full ${badge.dot}`} />
                  {badge.text}
                </span>

                {/* Fresh / Active Mode Toggle Pill */}
                {onToggleFreshUser && (
                  <button
                    onClick={onToggleFreshUser}
                    className={`text-[9px] font-mono font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full border transition cursor-pointer ${
                      isFreshUser
                        ? 'text-[#10B981] bg-[#10B981]/15 border-[#10B981]/30 hover:bg-[#10B981]/25'
                        : 'text-[#2B44E8] bg-[#2B44E8]/10 border-[#2B44E8]/20 hover:bg-[#2B44E8]/20'
                    }`}
                    title="Toggle between Fresh First-Time User and Active Analysis Mode"
                  >
                    {isFreshUser ? '🌿 Fresh User' : '⚡ Active Mode'}
                  </button>
                )}
              </div>
              <p className="text-[11px] text-[#5A5E72] font-mono">
                Safe balance, live rates &amp; smart bill check
              </p>
            </div>
          </div>

          {/* Mobile Mandate Trigger */}
          {onOpenMandateModal && (
            <button
              onClick={onOpenMandateModal}
              className="md:hidden px-3 py-1.5 rounded-full bg-[#131522] text-white text-[11px] font-medium flex items-center gap-1.5"
            >
              <Sparkles className="w-3.5 h-3.5 text-[#EB7951]" />
              Mandate
            </button>
          )}
        </div>

        {/* Right: Currency Dropdown, Android App Studio, Passkey & Bank Pills */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Location Hub Pill */}
          {onOpenLocationModal && (
            <button
              onClick={onOpenLocationModal}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/90 hover:bg-white border border-black/8 shadow-2xs text-[#141726] transition cursor-pointer"
              title={`Current Location Hub: ${activeHub.city}, ${activeHub.country} (${activeHub.currency})`}
            >
              <MapPin className="w-3.5 h-3.5 text-[#2B44E8]" />
              <span className="text-xs font-mono font-bold">{activeHub.city}</span>
              <span className="text-[10px] font-mono text-[#10B981] font-semibold hidden xl:inline">({activeHub.ruleTitle.split(' ')[0]})</span>
            </button>
          )}

          {/* Multi-Currency Dropdown Selector */}
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/90 border border-black/8 shadow-2xs">
            <span className="text-[10px] font-mono text-[#5A5E72] font-bold">Currency:</span>
            <select
              value={userBaseCurrency}
              onChange={(e) => onCurrencyChange && onCurrencyChange(e.target.value)}
              className="bg-transparent text-xs font-mono font-bold text-[#141726] focus:outline-none cursor-pointer"
            >
              <option value="AUD">AUD ($)</option>
              <option value="IDR">IDR (Rp)</option>
              <option value="USD">USD ($)</option>
              <option value="SGD">SGD (S$)</option>
              <option value="EUR">EUR (€)</option>
              <option value="GBP">GBP (£)</option>
              <option value="JPY">JPY (¥)</option>
            </select>
          </div>

          {/* Open Android Interactive Device Studio */}
          <a
            href="/android/preview.html"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#2B44E8] hover:bg-[#1f35c4] text-white text-[11px] font-semibold transition shadow-xs"
            title="Open the overhauled Android App Interactive Device Studio"
          >
            <Smartphone className="w-3.5 h-3.5 text-[#EABAA8]" />
            <span>Android Studio</span>
          </a>

          {/* Device Security Passkey Fingerprint */}
          <button
            onClick={onOpenMandateModal}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/85 hover:bg-white border border-black/6 text-[11px] text-[#141726] transition shadow-2xs"
            title="Device Security Passkey & Protection Mandate"
          >
            <KeyRound className="w-3.5 h-3.5 text-[#2B44E8]" />
            <span className="text-[#5A5E72] font-mono">Passkey:</span>
            <span className="font-mono font-semibold text-[#141726]">
              {userPublicKey.slice(0, 6)}…{userPublicKey.slice(-4)}
            </span>
          </button>

          {/* Sinking Pot Vault */}
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#EB7951]/12 border border-[#EB7951]/25 text-[11px] text-[#141726]">
            <Lock className="w-3.5 h-3.5 text-[#EB7951]" />
            <span className="text-[#5A5E72] font-medium">Escrow Pot:</span>
            <span className="font-mono font-bold text-[#141726]">
              {formatIdrInCurrency(potBalance, userBaseCurrency)}
            </span>
          </div>

          {/* Checking Account Balance */}
          <div className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full frosted-action-pill text-white text-[11px]">
            <Wallet className="w-3.5 h-3.5 text-[#EABAA8]" />
            <span className="text-white/75">Checking:</span>
            <span className="font-mono font-bold text-white">
              {formatIdrInCurrency(checkingBalance, userBaseCurrency)}
            </span>
          </div>

          {/* Settings & Activity Download Button */}
          {onOpenSettings && (
            <button
              onClick={onOpenSettings}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/90 hover:bg-white border border-black/8 text-[11px] font-semibold text-[#141726] transition shadow-2xs"
              title="Open Settings & Download Activity Receipt"
            >
              <Settings className="w-3.5 h-3.5 text-[#141726]" />
              <span>Settings</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
