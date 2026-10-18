import type React from 'react';
import { useState, useRef } from 'react';
import { ArrowRight, KeyRound, ShieldCheck, Navigation, Sparkles, X } from 'lucide-react';

interface OnboardingFlowProps {
  isOpen: boolean;
  onClose: () => void;
}

interface OnboardingCase {
  id: string;
  chipLabel: string;
  budgetLoad: string;
  ledgerSteps: [string, string, string, string];
  p1Prompt: string;
  p2Title: string;
  pill1Claim: string;
  pill1Truth: string;
  pill2Claim: string;
  pill2Truth: string;
  p2Cta: string;
  day1Price: string;
  day4Title: string;
  day4Price: string;
  day9Price: string;
  bufferLeft: string;
  editorialHighlight: string;
  pillLeft: string;
  pillRight: string;
  mascot1Tag: string;
  p4Orig: string;
  p4Cap: string;
  p4Status: string;
  p4Cta: string;
}

const ONBOARDING_CASES: OnboardingCase[] = [
  {
    id: 'laptop',
    chipLabel: '$1,200 Laptop',
    budgetLoad: '+$960 Safe Buffer',
    ledgerSteps: [
      'Bill: $1,200',
      'Extra Fee: +$120',
      'Day 4: $1,055 (-$145)',
      'Cap: $1,055 (+$265 Saved)',
    ],
    p1Prompt: '$1,200 Work Laptop',
    p2Title: '$1,200 Work Laptop',
    pill1Claim: '0% Plan · $10/mo Fee',
    pill1Truth: '+$120 Hidden Fee Found',
    pill2Claim: '$1,200 of $2,450/mo',
    pill2Truth: '$1,250 Buffer Safe',
    p2Cta: '$1,055 Valley (-$145) →',
    day1Price: '$1,200.00',
    day4Title: 'Best Buy Window',
    day4Price: '$1,055.00 (-$145)',
    day9Price: '$1,140.00',
    bufferLeft: '+$1,395 Buffer',
    editorialHighlight: '$1,055 valley',
    pillLeft: '-$145 Timing',
    pillRight: '-$120 Fee Saved',
    mascot1Tag: '-$120 Saved',
    p4Orig: '$1,320 Total',
    p4Cap: '$1,055 Cap',
    p4Status: 'Saved $265 total ($120 fee + $145 timing). Ready to lock.',
    p4Cta: 'Get Started ($1,055)',
  },
  {
    id: 'home',
    chipLabel: '$850 Home',
    budgetLoad: '+$1,600 Safe Buffer',
    ledgerSteps: [
      'Bill: $850',
      'Extra Fee: +$96',
      'Day 4: $740 (-$110)',
      'Cap: $740 (+$206 Saved)',
    ],
    p1Prompt: '$850 Home Upgrade',
    p2Title: '$850 Home Upgrade',
    pill1Claim: 'Pay-in-4 · $8/mo Fee',
    pill1Truth: '+$96 Hidden Fee Found',
    pill2Claim: '$850 of $2,450/mo',
    pill2Truth: '$1,600 Buffer Safe',
    p2Cta: '$740 Valley (-$110) →',
    day1Price: '$850.00',
    day4Title: 'Best Buy Window',
    day4Price: '$740.00 (-$110)',
    day9Price: '$815.00',
    bufferLeft: '+$1,710 Buffer',
    editorialHighlight: '$740 valley',
    pillLeft: '-$110 Timing',
    pillRight: '-$96 Fee Saved',
    mascot1Tag: '-$96 Saved',
    p4Orig: '$946 Total',
    p4Cap: '$740 Cap',
    p4Status: 'Saved $206 total ($96 fee + $110 timing). Ready to lock.',
    p4Cta: 'Get Started ($740)',
  },
  {
    id: 'scam',
    chipLabel: '$640 Alert',
    budgetLoad: 'Scam Shield',
    ledgerSteps: [
      'Alert: $640 Listing',
      'Wire Risk Blocked',
      'Verified: $565 (-$75)',
      'Escrow: $565 Protected',
    ],
    p1Prompt: '$640 Flash Listing',
    p2Title: '$640 Flash Listing',
    pill1Claim: '65% Off · Direct Wire',
    pill1Truth: 'Suspicious Wire Blocked',
    pill2Claim: '$640 Unprotected Wire',
    pill2Truth: 'Escrow Protected',
    p2Cta: '$565 Verified Store →',
    day1Price: '$640.00',
    day4Title: 'Verified Store Floor',
    day4Price: '$565.00 (-$75)',
    day9Price: '$615.00',
    bufferLeft: '+$1,885 Buffer',
    editorialHighlight: '$565 floor',
    pillLeft: '-$75 Verified',
    pillRight: '$640 Protected',
    mascot1Tag: 'Scam Blocked',
    p4Orig: '$640 Risk',
    p4Cap: '$565 Escrow',
    p4Status: 'Unverified wire blocked and $565 verified cap locked.',
    p4Cta: 'Get Started ($565)',
  },
];

export const OnboardingFlow: React.FC<OnboardingFlowProps> = ({ isOpen, onClose }) => {
  const [slide, setSlide] = useState<0 | 1 | 2 | 3>(0);
  const [caseIdx, setCaseIdx] = useState<number>(0);
  const [orbExcited, setOrbExcited] = useState(false);

  const [xray1, setXray1] = useState(false);
  const [xray2, setXray2] = useState(false);
  const [topoDay, setTopoDay] = useState<1 | 4 | 9>(4);
  const [mascotNote, setMascotNote] = useState<string | null>(null);
  const [pupilOffset, setPupilOffset] = useState({ x: 0, y: 0 });
  const touchStartX = useRef<number | null>(null);

  if (!isOpen) return null;

  const activeCase = ONBOARDING_CASES[caseIdx];
  const stepLabels = ['Budget', 'Truth', 'Timing', 'Vault'];

  const selectCase = (idx: number) => {
    setCaseIdx(idx);
    setXray1(false);
    setXray2(false);
    setMascotNote(null);
    setOrbExcited(true);
    setTimeout(() => setOrbExcited(false), 550);
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const dx = Math.max(-4, Math.min(4, ((e.clientX - rect.left) / rect.width - 0.5) * 9));
    const dy = Math.max(-3, Math.min(3, ((e.clientY - rect.top) / rect.height - 0.5) * 7));
    setPupilOffset({ x: dx, y: dy });
  };

  const handleTouchStart = (e: React.TouchEvent<HTMLDivElement>) => {
    touchStartX.current = e.touches[0].clientX;
  };

  const handleTouchEnd = (e: React.TouchEvent<HTMLDivElement>) => {
    if (touchStartX.current === null) return;
    const dx = e.changedTouches[0].clientX - touchStartX.current;
    touchStartX.current = null;
    if (dx < -45 && slide < 3) {
      setSlide((slide + 1) as 0 | 1 | 2 | 3);
    } else if (dx > 45 && slide > 0) {
      setSlide((slide - 1) as 0 | 1 | 2 | 3);
  }
  };

  return (
    <div
      onMouseMove={handleMouseMove}
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-[#131522]/75 backdrop-blur-xl animate-fadeIn"
    >
      {/* Unified Warm Muestra-64 Fluid Onboarding Container */}
      <div
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
        className="relative w-full max-w-[430px] h-[790px] max-h-[94vh] rounded-[46px] shadow-[0_32px_90px_rgba(20,23,38,0.45)] border-[3px] border-white/80 flex flex-col justify-between overflow-hidden select-none text-[#141726] muestra-bg"
      >
        {/* Top Fluid Pill Progress Bar + Skip */}
        <div className="px-5 pt-5 pb-1.5 flex items-center justify-between z-20">
          <div className="flex items-center gap-1 p-1 rounded-full soma-glass">
            {[0, 1, 2, 3].map((idx) => (
              <button
                key={idx}
                onClick={() => setSlide(idx as 0 | 1 | 2 | 3)}
                className={`px-3 py-1 rounded-full text-[10px] font-mono font-bold transition-all duration-300 ${
                  slide === idx
                    ? 'bg-[#131522] text-white shadow-xs'
                    : 'text-[#5A5E72] hover:text-[#141726]'
                }`}
              >
                {stepLabels[idx]}
              </button>
            ))}
          </div>

          <button
            onClick={onClose}
            className="px-3 py-1 rounded-full text-xs font-mono font-semibold flex items-center gap-1 soma-glass text-[#141726]/75 hover:text-[#141726] transition"
          >
            <span>Skip</span>
            <X className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Live Correlated Budget Strip */}
        <div className="px-5 pb-2 z-20">
          <div className="w-full px-3.5 py-2 rounded-2xl soma-glass flex items-center justify-between text-[10px] font-mono">
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#10B981]" />
              <span className="font-bold text-[#141726]">$2,450/mo</span>
            </div>
            <span className="text-[#5A5E72]">→</span>
            <span className="font-bold text-[#2B44E8]">{activeCase.ledgerSteps[slide]}</span>
          </div>
        </div>

        {/* Fluid Horizontal 4-Page Track */}
        <div className="relative flex-1 w-full overflow-hidden">
          <div
            className="flex h-full w-[400%] transition-transform duration-500 ease-[cubic-bezier(0.22,1,0.36,1)]"
            style={{ transform: `translateX(-${slide * 25}%)` }}
          >
            {/* PAGE 1: Budget Orb */}
            <div className="w-1/4 h-full px-6 pb-6 flex flex-col items-center justify-between">
              <div className="my-auto flex flex-col items-center z-10">
                <div
                  onClick={() => selectCase((caseIdx + 1) % ONBOARDING_CASES.length)}
                  className={`relative w-44 h-44 rounded-full flex items-center justify-center cursor-pointer transition-transform duration-500 ${
                    orbExcited ? 'scale-110' : 'hover:scale-105'
                  }`}
                  style={{
                    background:
                      'radial-gradient(circle at 30% 25%, #FFFFFF 0%, #FDF6E4 32%, #EABAA8 65%, #2B44E8 100%)',
                    boxShadow:
                      '0 24px 55px rgba(43, 68, 232, 0.24), 0 10px 28px rgba(235, 121, 81, 0.22), inset 0 3px 10px rgba(255, 255, 255, 0.95)',
                  }}
                >
                  <div
                    className="absolute inset-2 rounded-full border-2 border-[#2B44E8]/35 animate-spin"
                    style={{ animationDuration: '9s' }}
                  />
                  <div
                    className="absolute inset-3.5 rounded-full border-2 border-[#EB7951]/45 animate-spin"
                    style={{ animationDuration: '12s', animationDirection: 'reverse' }}
                  />
                  <div className="relative z-10 text-center px-2">
                    <span className="text-[9px] font-mono uppercase tracking-widest text-[#5A5E72] block">
                      SAFE BUFFER
                    </span>
                    <span className="text-lg font-black font-mono text-[#141726] tracking-tight block mt-0.5">
                      $2,450.00
                    </span>
                    <span className="text-[9px] font-mono font-bold text-[#2B44E8] block mt-0.5">
                      {activeCase.budgetLoad}
                    </span>
                  </div>
                </div>

                <h2 className="mt-6 text-2xl font-extrabold text-[#141726] text-center leading-tight tracking-tight">
                  Guard every dollar.
                </h2>

                <div className="mt-4 flex flex-wrap justify-center gap-1.5">
                  {ONBOARDING_CASES.map((c, idx) => (
                    <button
                      key={c.id}
                      onClick={() => selectCase(idx)}
                      className={`px-3 py-1.5 rounded-full text-[10px] font-mono transition ${
                        caseIdx === idx
                          ? 'bg-[#131522] text-white font-bold shadow-xs'
                          : 'soma-glass text-[#141726]'
                      }`}
                    >
                      {c.chipLabel}
                    </button>
                  ))}
                </div>
              </div>

              <button
                onClick={() => setSlide(1)}
                className="w-full h-14 px-5 rounded-[26px] soma-glass flex items-center justify-between transition active:scale-98"
              >
                <span className="text-xs font-bold text-[#141726] truncate">
                  {activeCase.p1Prompt}
                </span>
                <div className="w-9 h-9 rounded-full bg-[#131522] text-white flex items-center justify-center shrink-0">
                  <Sparkles className="w-4 h-4 text-[#EABAA8]" />
                </div>
              </button>
            </div>

            {/* PAGE 2: Hidden Fee X-Ray */}
            <div className="w-1/4 h-full px-6 pb-6 flex flex-col items-center justify-between">
              <div
                onClick={() => {
                  setXray1(!xray1);
                  setXray2(!xray2);
                }}
                className="mt-2 w-52 h-44 rounded-[42%_58%_54%_46%/44%_38%_62%_56%] flex flex-col items-center justify-center p-5 text-center cursor-pointer transition-transform active:scale-95 shadow-lg"
                style={{
                  background:
                    'radial-gradient(circle at 26% 24%, #EB7951 0%, rgba(235, 121, 81, 0.75) 38%, transparent 72%), radial-gradient(circle at 78% 30%, #2B44E8 0%, rgba(76, 106, 181, 0.7) 44%, transparent 75%), radial-gradient(circle at 24% 80%, #EABAA8 0%, #131522 100%)',
                }}
              >
                <div className="grid grid-cols-4 gap-1.5 mb-2">
                  <span className="w-2 h-2 rounded-full bg-transparent" />
                  <span className="w-2.5 h-2.5 rounded-full bg-white" />
                  <span className="w-2.5 h-2.5 rounded-full bg-white/80" />
                  <span className="w-2 h-2 rounded-full bg-transparent" />
                  <span className="w-2.5 h-2.5 rounded-full bg-white" />
                  <span className="w-2.5 h-2.5 rounded-full bg-[#FDF6E4]" />
                  <span className="w-2.5 h-2.5 rounded-full bg-white" />
                  <span className="w-2.5 h-2.5 rounded-full bg-white/90" />
                </div>
                <p className="text-sm font-extrabold text-white leading-snug">
                  {activeCase.p2Title}
                </p>
              </div>

              <div className="w-full rounded-[34px] soma-glass p-5 flex flex-col items-center text-center">
                <h3 className="text-lg font-extrabold text-[#141726] tracking-tight">
                  Hidden Fee Check
                </h3>

                <button
                  onClick={() => setXray1(!xray1)}
                  className={`mt-3 w-full py-3 px-4 rounded-full border flex items-center justify-between text-xs font-mono transition-all ${
                    xray1
                      ? 'bg-[#131522] text-white border-[#EB7951]'
                      : 'bg-white/85 text-[#141726] border-[#141726]/10'
                  }`}
                >
                  <span className="truncate pr-2">
                    {xray1 ? activeCase.pill1Truth : activeCase.pill1Claim}
                  </span>
                  <span
                    className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full shrink-0 ${
                      xray1 ? 'bg-[#EB7951] text-white' : 'bg-[#EB7951]/15 text-[#EB7951]'
                    }`}
                  >
                    {xray1 ? 'TRUTH' : 'FEE'}
                  </span>
                </button>

                <button
                  onClick={() => setXray2(!xray2)}
                  className={`mt-2 w-full py-3 px-4 rounded-full border flex items-center justify-between text-xs font-mono transition-all ${
                    xray2
                      ? 'bg-[#2B44E8] text-white border-[#2B44E8]'
                      : 'bg-white/85 text-[#141726] border-[#141726]/10'
                  }`}
                >
                  <span className="truncate pr-2">
                    {xray2 ? activeCase.pill2Truth : activeCase.pill2Claim}
                  </span>
                  <span
                    className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full shrink-0 ${
                      xray2 ? 'bg-[#FDF6E4] text-[#131522]' : 'bg-[#2B44E8]/15 text-[#2B44E8]'
                    }`}
                  >
                    {xray2 ? 'SAFE' : 'BUFFER'}
                  </span>
                </button>

                <button
                  onClick={() => setSlide(2)}
                  className="mt-4 w-full py-3.5 rounded-full bg-[#131522] hover:bg-[#2B44E8] text-white text-xs font-bold tracking-wide shadow-md transition"
                >
                  {activeCase.p2Cta}
                </button>
              </div>
            </div>

            {/* PAGE 3: Smart Buy Timing */}
            <div className="w-1/4 h-full px-6 pb-6 flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#2B44E8]" />
                  <span className="text-[10px] font-mono font-bold text-[#141726]/70">
                    14-DAY WINDOW
                  </span>
                </div>
                <div className="flex items-center gap-1 soma-glass rounded-full p-1">
                  {([1, 4, 9] as const).map((d) => (
                    <button
                      key={d}
                      onClick={() => setTopoDay(d)}
                      className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold transition ${
                        topoDay === d ? 'bg-[#2B44E8] text-white' : 'text-[#5A5E72]'
                      }`}
                    >
                      Day {d}
                    </button>
                  ))}
                </div>
              </div>

              <div className="relative flex flex-col items-center my-auto">
                <div className="z-20 -mb-6 px-5 py-2.5 rounded-[24px] soma-glass flex items-center gap-3.5">
                  <div className="text-left">
                    <div className="text-[9px] font-mono uppercase tracking-wider text-[#5A5E72]">
                      Day 0{topoDay}
                    </div>
                    <div className="text-xs font-extrabold text-[#141726]">
                      {topoDay === 4 ? 'Buy Window' : topoDay === 1 ? 'Hold' : 'Rebound'}
                    </div>
                  </div>
                  <span className="h-5 w-[1px] bg-[#141726]/15" />
                  <span className="text-xs font-mono font-bold text-[#2B44E8]">
                    {topoDay === 4 ? 'Best Day' : topoDay === 1 ? 'Wait' : 'Higher'}
                  </span>
                </div>

                <div
                  onClick={() => setTopoDay(topoDay === 1 ? 4 : topoDay === 4 ? 9 : 1)}
                  className="w-48 h-48 rounded-full relative flex flex-col items-center justify-center cursor-pointer transition-transform active:scale-95 overflow-hidden"
                  style={{
                    background:
                      'repeating-radial-gradient(circle at 52% 48%, rgba(43, 68, 232, 0.08) 0px, rgba(43, 68, 232, 0.08) 1px, transparent 1px, transparent 14px), radial-gradient(circle at 50% 42%, #FFFFFF 0%, #F4F0EA 58%, #E6DFD5 100%)',
                    boxShadow:
                      '0 20px 45px -15px rgba(20, 23, 38, 0.14), inset 0 2px 4px rgba(255, 255, 255, 0.95)',
                  }}
                >
                  <div className="w-7 h-7 rounded-full bg-[#2B44E8]/15 border border-[#2B44E8] flex items-center justify-center text-[#2B44E8] text-[10px] font-mono font-bold">
                    ●
                  </div>
                  <div className="mt-2.5 text-center relative z-10 px-3">
                    <div className="text-xs font-extrabold text-[#141726]">
                      {topoDay === 4
                        ? activeCase.day4Title
                        : topoDay === 1
                        ? 'Wait for Drop'
                        : 'Rebound'}
                    </div>
                    <div className="text-sm font-mono font-black text-[#2B44E8]">
                      {topoDay === 4
                        ? activeCase.day4Price
                        : topoDay === 1
                        ? activeCase.day1Price
                        : activeCase.day9Price}
                    </div>
                  </div>
                </div>

                <div className="w-full flex items-center justify-between px-2 mt-3">
                  <div className="flex items-center -space-x-2">
                    <span className="w-7 h-7 rounded-full bg-[#131522] text-white text-[9px] font-mono font-bold flex items-center justify-center border-2 border-[#FDF6E4]">
                      Fee
                    </span>
                    <span className="w-7 h-7 rounded-full bg-[#2B44E8] text-white text-[9px] font-mono font-bold flex items-center justify-center border-2 border-[#FDF6E4]">
                      Safe
                    </span>
                    <span className="w-7 h-7 rounded-full bg-[#EB7951] text-white text-[9px] font-mono font-bold flex items-center justify-center border-2 border-[#FDF6E4]">
                      Lock
                    </span>
                  </div>
                  <span className="text-[11px] font-mono font-semibold text-[#5A5E72]">
                    {activeCase.bufferLeft}
                  </span>
                </div>
              </div>

              <div className="px-1">
                <h2 className="text-2xl leading-tight tracking-tight text-[#141726] font-light">
                  Catch your{' '}
                  <span className="font-serif italic font-black text-[#2B44E8]">
                    {activeCase.editorialHighlight}
                  </span>
                </h2>
              </div>

              <div className="flex items-center gap-3">
                <div
                  onClick={() => setTopoDay(topoDay === 1 ? 4 : topoDay === 4 ? 9 : 1)}
                  className="flex-1 h-14 rounded-[26px] soma-glass px-4 flex items-center justify-between cursor-pointer"
                >
                  <span className="text-xs font-mono font-bold text-[#10B981]">
                    {activeCase.pillLeft}
                  </span>
                  <span className="h-4 w-[1.5px] bg-[#2B44E8]" />
                  <span className="text-xs font-mono font-semibold text-[#141726]">
                    {activeCase.pillRight}
                  </span>
                </div>
                <button
                  onClick={() => setSlide(3)}
                  className="w-16 h-14 rounded-[26px] bg-[#131522] hover:bg-[#2B44E8] text-white flex items-center justify-center shadow-lg transition"
                >
                  <Navigation className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* PAGE 4: Cryptographic Mandate & Guardians */}
            <div className="w-1/4 h-full px-5 pb-6 flex flex-col justify-between">
              <div className="relative w-full h-52 mt-1">
                <div
                  onClick={() =>
                    setMascotNote('Hidden fee protection & security passkey ready.')
                  }
                  className="absolute left-10 top-1 w-28 h-28 -rotate-12 rounded-b-[42px] rounded-t-[18px] soma-glass flex flex-col items-center justify-between p-3 cursor-pointer hover:scale-105 transition"
                >
                  <span className="text-[9px] font-mono font-bold uppercase text-[#EB7951]">
                    {activeCase.mascot1Tag}
                  </span>
                  <div className="flex items-center gap-1.5 border-b-2 border-[#141726] pb-0.5">
                    <div className="w-4 h-3 rounded-t-full bg-[#141726] flex items-center justify-center">
                      <span
                        className="w-1.5 h-1.5 rounded-full bg-white transition-transform"
                        style={{
                          transform: `translate(${pupilOffset.x}px, ${pupilOffset.y}px)`,
                        }}
                      />
                    </div>
                    <div className="w-4 h-3 rounded-t-full bg-[#141726] flex items-center justify-center">
                      <span
                        className="w-1.5 h-1.5 rounded-full bg-white transition-transform"
                        style={{
                          transform: `translate(${pupilOffset.x}px, ${pupilOffset.y}px)`,
                        }}
                      />
                    </div>
                  </div>
                </div>

                <div
                  onClick={() =>
                    setMascotNote('Private details stay on your device.')
                  }
                  className="absolute right-2 top-8 w-32 h-26 rotate-3 rounded-[32px] soma-glass flex flex-col items-center justify-center p-3 cursor-pointer hover:scale-105 transition"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-4 h-3.5 rounded-t-full bg-[#2B44E8] flex items-center justify-center">
                      <span
                        className="w-1.5 h-1.5 rounded-full bg-white transition-transform"
                        style={{
                          transform: `translate(${pupilOffset.x}px, ${pupilOffset.y}px)`,
                        }}
                      />
                    </div>
                    <div className="w-4 h-3.5 rounded-t-full bg-[#2B44E8] flex items-center justify-center">
                      <span
                        className="w-1.5 h-1.5 rounded-full bg-white transition-transform"
                        style={{
                          transform: `translate(${pupilOffset.x}px, ${pupilOffset.y}px)`,
                        }}
                      />
                    </div>
                  </div>
                  <span className="mt-2 text-[9px] font-mono font-bold text-[#2B44E8] bg-[#2B44E8]/10 px-2 py-0.5 rounded-full">
                    Private
                  </span>
                </div>

                <div
                  onClick={() =>
                    setMascotNote('Suspiciously cheap scam listings are automatically blocked.')
                  }
                  className="absolute left-2 bottom-0 w-34 h-28 -rotate-6 rounded-full soma-glass flex flex-col items-center justify-center p-3 cursor-pointer hover:scale-105 transition"
                >
                  <div className="flex items-center gap-2">
                    <div className="w-5 h-5 rounded-full bg-[#141726] flex items-center justify-center">
                      <span
                        className="w-2 h-2 rounded-full bg-white transition-transform"
                        style={{
                          transform: `translate(${pupilOffset.x}px, ${pupilOffset.y}px)`,
                        }}
                      />
                    </div>
                    <div className="w-5 h-5 rounded-full bg-[#141726] flex items-center justify-center">
                      <span
                        className="w-2 h-2 rounded-full bg-white transition-transform"
                        style={{
                          transform: `translate(${pupilOffset.x}px, ${pupilOffset.y}px)`,
                        }}
                      />
                    </div>
                  </div>
                  <span className="mt-1.5 text-[9px] font-mono font-bold text-[#141726] bg-[#FDF6E4] px-2 py-0.5 rounded-full border border-[#141726]/10">
                    Scam Shield
                  </span>
                </div>
              </div>

              <div className="w-full rounded-[32px] soma-glass p-5 flex flex-col justify-between">
                <div>
                  <div className="mb-2.5 px-3 py-2 rounded-2xl bg-white/80 border border-[#141726]/8 flex items-center justify-between text-[10px] font-mono">
                    <span className="text-[#5A5E72] line-through">{activeCase.p4Orig}</span>
                    <span className="text-[#2B44E8] font-bold">→ Verified</span>
                    <span className="px-2 py-0.5 rounded-full bg-[#10B981]/15 text-[#065F46] font-extrabold">
                      {activeCase.p4Cap}
                    </span>
                  </div>

                  <h2 className="text-xl leading-tight tracking-tight font-extrabold text-[#141726]">
                    Protected by Security Passkey.
                  </h2>
                  <p className="mt-1.5 text-xs text-[#5A5E72] leading-relaxed">
                    {mascotNote || activeCase.p4Status}
                  </p>
                </div>

                <div className="mt-4 flex items-center gap-2">
                  <button
                    onClick={() =>
                      setMascotNote('Device Passkey never leaves your browser.')
                    }
                    className="w-11 h-12 rounded-2xl bg-white/85 hover:bg-[#2B44E8]/15 border border-[#141726]/10 flex items-center justify-center text-[#2B44E8] transition"
                    title="Security Passkey"
                  >
                    <KeyRound className="w-5 h-5" />
                  </button>
                  <button
                    onClick={() =>
                      setMascotNote('Zero Data Retention: PII masked locally.')
                    }
                    className="w-11 h-12 rounded-2xl bg-white/85 hover:bg-[#10B981]/15 border border-[#141726]/10 flex items-center justify-center text-[#141726] transition"
                    title="Zero-PII"
                  >
                    <ShieldCheck className="w-5 h-5" />
                  </button>
                  <button
                    onClick={onClose}
                    className="flex-1 h-12 rounded-2xl bg-[#131522] hover:bg-[#2B44E8] text-white font-bold text-xs tracking-wide shadow-md flex items-center justify-center gap-1.5 transition"
                  >
                    <span>{activeCase.p4Cta}</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
