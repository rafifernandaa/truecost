import type React from 'react';
import { useState } from 'react';
import {
  Clock,
  Wallet,
  CheckCircle2,
  Pause,
  MinusCircle,
  EyeOff,
  BadgeCheck,
  KeyRound,
  ShieldAlert,
  Sparkles,
  ChevronRight,
} from 'lucide-react';

export type NavSection = 'all' | 'copilot' | 'replay' | 'vault';
export type AgentAutonomyTier = 'tier2_online' | 'tier1_idle' | 'tier3_dnd' | 'tier0_invisible';

interface MorphingBottomDockProps {
  activeSection: NavSection;
  onSelectSection: (section: NavSection) => void;
  autonomyTier: AgentAutonomyTier;
  onSelectAutonomyTier: (tier: AgentAutonomyTier) => void;
  checkingBalance: number;
  potBalance: number;
  activeMandate: any | null;
  onOpenMandateModal: () => void;
  onTriggerScamSimulation: () => void;
  transactionsCount: number;
}

const TIER_CONFIG: Record<
  AgentAutonomyTier,
  {
    label: string;
    shortStatus: string;
    badgeBg: string;
    badgeText: string;
    description: string;
    icon: React.FC<{ className?: string }>;
  }
> = {
  tier2_online: {
    label: 'Auto-Buy Mode · Within Cap',
    shortStatus: 'Auto-Buy Mode',
    badgeBg: 'bg-[#10B981]',
    badgeText: 'text-white',
    description: 'Buys automatically when price hits your target cap',
    icon: CheckCircle2,
  },
  tier1_idle: {
    label: 'Hold Mode · Wait for Price Drop',
    shortStatus: 'Hold Mode',
    badgeBg: 'bg-[#F59E0B]',
    badgeText: 'text-[#141726]',
    description: 'Reserves funds in escrow until price drops',
    icon: Pause,
  },
  tier3_dnd: {
    label: 'Ask First · Confirm Every Time',
    shortStatus: 'Ask First',
    badgeBg: 'bg-[#EB7951]',
    badgeText: 'text-white',
    description: 'Requires your confirmation before any payment',
    icon: MinusCircle,
  },
  tier0_invisible: {
    label: 'Check Only · Read-Only',
    shortStatus: 'Check Only',
    badgeBg: 'bg-[#CBD5E1]',
    badgeText: 'text-[#141726]',
    description: 'Checks prices and fees without moving money',
    icon: EyeOff,
  },
};

export const MorphingBottomDock: React.FC<MorphingBottomDockProps> = ({
  onSelectSection,
  autonomyTier,
  onSelectAutonomyTier,
  checkingBalance,
  potBalance,
  activeMandate,
  onOpenMandateModal,
  onTriggerScamSimulation,
  transactionsCount,
}) => {
  // Single unified morphing Circle <-> Pill dock (matches Screenshot 1)
  const [expandedItem, setExpandedItem] = useState<'copilot' | 'replay' | 'vault' | 'agent'>('copilot');
  const [isStatusSheetOpen, setIsStatusSheetOpen] = useState(false);

  const currentTier = TIER_CONFIG[autonomyTier];
  const TierIcon = currentTier.icon;

  const handleTabPress = (target: 'copilot' | 'replay' | 'vault') => {
    setExpandedItem(target);
    setIsStatusSheetOpen(false);
    onSelectSection(target);
  };

  const handleAgentPress = () => {
    if (expandedItem === 'agent') {
      setIsStatusSheetOpen((prev) => !prev);
    } else {
      setExpandedItem('agent');
      setIsStatusSheetOpen(true);
    }
  };

  return (
    <>
      {/* Backdrop when status popover is open */}
      {isStatusSheetOpen && (
        <div
          className="fixed inset-0 z-40 bg-[#141726]/10 backdrop-blur-[2px] transition-opacity duration-300"
          onClick={() => setIsStatusSheetOpen(false)}
        />
      )}

      <div className="fixed bottom-5 left-1/2 -translate-x-1/2 z-50 flex flex-col items-center w-full max-w-[95vw] sm:max-w-fit pointer-events-none">
        {/* Popover Status & Account Switcher Sheet */}
        <div
          className={`pointer-events-auto mb-3 w-[340px] sm:w-[380px] rounded-[30px] p-3 dock-glass spring-popover origin-bottom ${
            isStatusSheetOpen
              ? 'opacity-100 translate-y-0 scale-100'
              : 'opacity-0 translate-y-6 scale-90 pointer-events-none h-0 overflow-hidden mb-0 p-0 border-0'
          }`}
        >
          <div className="px-2 pt-1 pb-2 flex items-center justify-between">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-[#5A5E72]">
              Autonomy Guardrail
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#2B44E8]/10 text-[#2B44E8] font-medium">
              Passkey Verified
            </span>
          </div>

          <div className="space-y-1.5 bg-white/80 rounded-[22px] p-2 border border-white/90 shadow-xs">
            {(Object.keys(TIER_CONFIG) as AgentAutonomyTier[]).map((tierKey) => {
              const item = TIER_CONFIG[tierKey];
              const ItemIcon = item.icon;
              const isSelected = autonomyTier === tierKey;

              return (
                <button
                  key={tierKey}
                  onClick={() => {
                    onSelectAutonomyTier(tierKey);
                    setIsStatusSheetOpen(false);
                  }}
                  className={`w-full flex items-center justify-between p-2 rounded-[16px] text-left transition-all duration-200 ${
                    isSelected
                      ? 'bg-[#131522] text-white shadow-sm'
                      : 'hover:bg-[#F4F0EA]/80 text-[#141726]'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center ${item.badgeBg} ${item.badgeText} shadow-xs shrink-0`}
                    >
                      <ItemIcon className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-xs font-semibold leading-tight">{item.label}</div>
                      <div
                        className={`text-[10px] mt-0.5 ${
                          isSelected ? 'text-white/70' : 'text-[#5A5E72]'
                        }`}
                      >
                        {item.description}
                      </div>
                    </div>
                  </div>
                  {isSelected && (
                    <span className="w-2 h-2 rounded-full bg-[#EB7951] mr-2 shrink-0" />
                  )}
                </button>
              );
            })}
          </div>

          <div className="mt-2.5 px-2 pt-1">
            <div className="flex items-center justify-between text-[11px] font-semibold uppercase tracking-wider text-[#5A5E72] mb-1.5">
              <span>Mandate & Vault Controls</span>
              <span className="px-1.5 py-0.5 rounded-full bg-[#EB7951] text-white text-[10px] font-mono">
                {transactionsCount} logs
              </span>
            </div>

            <div className="space-y-1.5">
              <button
                onClick={() => {
                  setIsStatusSheetOpen(false);
                  onOpenMandateModal();
                }}
                className="w-full flex items-center justify-between p-2.5 rounded-[18px] bg-white/75 hover:bg-white border border-white/90 transition text-left group"
              >
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-full bg-[#2B44E8]/12 text-[#2B44E8] flex items-center justify-center font-mono text-xs font-bold">
                    <KeyRound className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-[#141726] flex items-center gap-1">
                      <span>{activeMandate ? 'Update Signed Mandate' : 'Sign Intent Mandate'}</span>
                      <BadgeCheck className="w-3.5 h-3.5 text-[#2B44E8]" />
                    </div>
                    <div className="text-[10px] font-mono text-[#5A5E72]">
                      Pot: Rp {potBalance.toLocaleString('id-ID')} · Chk: Rp {(checkingBalance / 1000000).toFixed(1)}M
                    </div>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-[#5A5E72] group-hover:translate-x-0.5 transition" />
              </button>

              <button
                onClick={() => {
                  setIsStatusSheetOpen(false);
                  onTriggerScamSimulation();
                }}
                className="w-full flex items-center justify-between p-2.5 rounded-[18px] bg-[#EB7951]/12 hover:bg-[#EB7951]/20 border border-[#EB7951]/25 transition text-left group"
              >
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-full bg-[#EB7951] text-white flex items-center justify-center">
                    <ShieldAlert className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-[#141726]">
                      Test Scam Protection
                    </div>
                    <div className="text-[10px] font-mono text-[#5A5E72]">
                      Preview 10-second safety lock on suspicious offers
                    </div>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-[#EB7951] group-hover:translate-x-0.5 transition" />
              </button>
            </div>
          </div>
        </div>

        {/* SINGLE UNIFIED MORPHING CIRCLE <-> PILL CAPSULE DOCK (Screenshot 1) */}
        <nav
          aria-label="TrueCost Morphing Bottom Navigation"
          className="pointer-events-auto dock-glass rounded-[38px] p-2 flex items-center gap-2 spring-morph"
        >
          {/* Tab 1: TrueCost Co-Pilot */}
          <button
            onClick={() => handleTabPress('copilot')}
            className={`h-13 spring-morph flex items-center overflow-hidden border shrink-0 active:scale-[0.98] ${
              expandedItem === 'copilot'
                ? 'w-[215px] sm:w-[245px] rounded-[26px] bg-white border-black/5 px-2.5 shadow-sm'
                : 'w-13 rounded-full bg-white/85 hover:bg-white border-black/5 justify-center shadow-xs'
            }`}
          >
            <div
              className={`w-9 h-9 rounded-full flex flex-col items-center justify-center shrink-0 transition-colors ${
                expandedItem === 'copilot'
                  ? 'bg-[#131522] text-white'
                  : 'bg-transparent text-[#141726]'
              }`}
            >
              <span className="font-serif font-black text-[11px] leading-none tracking-tighter">
                true
              </span>
              <span className="font-serif font-bold text-[10px] leading-none tracking-tight text-[#EB7951]">
                cost
              </span>
            </div>

            {expandedItem === 'copilot' && (
              <div className="ml-2.5 text-left min-w-0 flex-1 animate-in fade-in duration-200">
                <div className="flex items-center gap-1">
                  <span className="text-xs font-bold text-[#141726] truncate">
                    TrueCost Home
                  </span>
                  <BadgeCheck className="w-3.5 h-3.5 text-[#2B44E8] shrink-0 fill-[#2B44E8]/15" />
                </div>
                <div className="text-[11px] text-[#5A5E72] truncate font-medium">
                  Rp 17.58M · Optimal Buy
                </div>
              </div>
            )}
          </button>

          {/* Tab 2: Time-Travel Replay */}
          <button
            onClick={() => handleTabPress('replay')}
            className={`h-13 spring-morph flex items-center overflow-hidden border shrink-0 active:scale-[0.98] ${
              expandedItem === 'replay'
                ? 'w-[210px] sm:w-[235px] rounded-[26px] bg-[#131522] text-white border-[#131522] px-3 shadow-md'
                : 'w-13 rounded-full bg-white/85 hover:bg-white text-[#141726] border-black/5 justify-center shadow-xs'
            }`}
          >
            <div
              className={`w-9 h-9 rounded-full flex items-center justify-center shrink-0 ${
                expandedItem === 'replay'
                  ? 'bg-[#2B44E8] text-white'
                  : 'bg-transparent text-[#141726]'
              }`}
            >
              <Clock className="w-4.5 h-4.5" />
            </div>

            {expandedItem === 'replay' && (
              <div className="ml-2.5 text-left min-w-0 flex-1 animate-in fade-in duration-200">
                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-bold text-white truncate">14d Price Replay</span>
                  <span className="text-[9px] font-mono px-1.5 py-0.5 rounded-full bg-[#EB7951] text-white font-semibold">
                    -11.4%
                  </span>
                </div>
                <div className="text-[11px] text-white/70 truncate font-mono">
                  Saved Rp 2.1M vs Naive
                </div>
              </div>
            )}
          </button>

          {/* Tab 3: Sandbox Vault & Ledger */}
          <button
            onClick={() => handleTabPress('vault')}
            className={`h-13 spring-morph flex items-center overflow-hidden border shrink-0 active:scale-[0.98] ${
              expandedItem === 'vault'
                ? 'w-[210px] sm:w-[235px] rounded-[26px] bg-white border-black/5 px-3 shadow-sm'
                : 'w-13 rounded-full bg-white/85 hover:bg-white text-[#141726] border-black/5 justify-center shadow-xs'
            }`}
          >
            <div
              className={`w-9 h-9 rounded-full flex items-center justify-center shrink-0 ${
                expandedItem === 'vault'
                  ? 'bg-[#EB7951] text-white'
                  : 'bg-transparent text-[#141726]'
              }`}
            >
              <Wallet className="w-4.5 h-4.5" />
            </div>

            {expandedItem === 'vault' && (
              <div className="ml-2.5 text-left min-w-0 flex-1 animate-in fade-in duration-200">
                <div className="flex items-center gap-1">
                  <span className="text-xs font-bold text-[#141726] truncate">
                    Vault & Audit Trail
                  </span>
                </div>
                <div className="text-[11px] text-[#5A5E72] truncate font-mono">
                  Rp {(checkingBalance / 1000000).toFixed(1)}M · {transactionsCount} Events
                </div>
              </div>
            )}
          </button>

          {/* Rightmost Item: AP2 Agent Profile & Live Autonomy Status */}
          <button
            onClick={handleAgentPress}
            className={`h-13 spring-morph flex items-center justify-between overflow-hidden border shrink-0 active:scale-[0.98] ${
              expandedItem === 'agent'
                ? 'w-[215px] sm:w-[245px] rounded-[26px] bg-white border-black/5 pl-2 pr-2.5 shadow-sm'
                : 'w-13 rounded-full bg-white hover:bg-[#FAF8F5] border-black/5 justify-center shadow-xs relative'
            }`}
          >
            <div className="relative shrink-0">
              <div className="w-9 h-9 rounded-full muestra-hero-orb flex items-center justify-center text-white font-semibold text-xs shadow-inner border border-white/60">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              {expandedItem !== 'agent' && (
                <span
                  className={`absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 rounded-full border-2 border-white ${currentTier.badgeBg}`}
                />
              )}
            </div>

            {expandedItem === 'agent' && (
              <>
                <div className="ml-2.5 text-left min-w-0 flex-1 animate-in fade-in duration-200">
                  <div className="text-xs font-bold text-[#141726] truncate">Auto-Guard</div>
                  <div className="text-[11px] text-[#5A5E72] truncate font-medium">
                    {currentTier.shortStatus}
                  </div>
                </div>

                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${currentTier.badgeBg} ${currentTier.badgeText} shadow-xs`}
                >
                  <TierIcon className="w-4 h-4" />
                </div>
              </>
            )}
          </button>
        </nav>
      </div>
    </>
  );
};
