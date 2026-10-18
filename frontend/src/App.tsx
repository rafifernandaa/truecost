import { useState, useEffect } from 'react';
import nacl from 'tweetnacl';
import { Navbar } from './components/Navbar';
import { OneNumberCard, type ProductScenario } from './components/OneNumberCard';
import { ScamInterventionModal } from './components/ScamInterventionModal';
import { MandateModal } from './components/MandateModal';
import { AuditTrailView } from './components/AuditTrailView';
import { ReplaySimulator } from './components/ReplaySimulator';
import {
  MorphingBottomDock,
  type NavSection,
  type AgentAutonomyTier,
} from './components/MorphingBottomDock';
import { OnboardingFlow } from './components/OnboardingFlow';
import { getOrCreateUserKeyPair, type UserKeyPair, toHexString } from './lib/crypto';
import { formatIdrInCurrency, FX_TO_IDR } from './lib/currency';
import { ShieldCheck, KeyRound, ArrowRight, Sparkles, Layers, Download, Settings, X, CheckCircle2, MapPin, Compass } from 'lucide-react';
import { LOCATION_HUBS } from './lib/location';


const PRODUCT_SCENARIOS: ProductScenario[] = [
  {
    id: 'thinkpad_au',
    badge: 'ThinkPad T14s (AUD → IDR)',
    itemTitle: 'Lenovo ThinkPad T14s Gen 4 (AMD Ryzen 7 PRO, 16GB RAM, 512GB SSD)',
    merchantName: 'Lenovo Official Store Australia · Cross-Border',
    stickerPrice: 1580,
    stickerCurrency: 'AUD',
    trueCost: 17582248,
    targetCurrency: 'IDR',
    bnplBreakdown: {
      tenorMonths: 6,
      nominalApr: 0.18,
      effectiveAnnualRate: 0.195,
      totalFinanceCharge: 450000,
      isPredatory: false,
    },
    landedCostBreakdown: {
      spotFxRate: 10400,
      effectiveFxRate: 10660,
      fxMarkupCost: 410800,
      totalCustomsTaxes: 2423728,
      touristTaxRefund: 1684280,
    },
    optimalStopping: {
      decision: 'BUY',
      reservationPrice: 16900000,
      percentileRank: 16.7,
      daysLeft: 10,
      rationale:
        'Current pricing is near the 14-day low for this model. Waiting longer is unlikely to unlock a deeper discount before your 10-day window ends.',
    },
  },
  {
    id: 'macbook_sg',
    badge: 'MacBook Air M3 (SGD → IDR)',
    itemTitle: 'Apple MacBook Air 13" M3 Chip (16GB Unified Memory, 512GB SSD)',
    merchantName: 'Apple Orchard Road Singapore · Tourist Hand-Carry',
    stickerPrice: 1899,
    stickerCurrency: 'SGD',
    trueCost: 23415600,
    targetCurrency: 'IDR',
    bnplBreakdown: {
      tenorMonths: 12,
      nominalApr: 0.24,
      effectiveAnnualRate: 0.298,
      totalFinanceCharge: 1680000,
      isPredatory: true,
    },
    landedCostBreakdown: {
      spotFxRate: 11800,
      effectiveFxRate: 12095,
      fxMarkupCost: 560205,
      totalCustomsTaxes: 2154800,
      touristTaxRefund: 1707605,
    },
    optimalStopping: {
      decision: 'WAIT',
      reservationPrice: 22100000,
      percentileRank: 62.4,
      daysLeft: 12,
      rationale:
        'Current price is above our Rp 22.10M target buy price. Autopilot recommends holding your Sinking Pot funds for the upcoming promo sale.',
    },
  },
  {
    id: 'sony_jp',
    badge: 'Sony WH-1000XM5 (JPY → IDR)',
    itemTitle: 'Sony WH-1000XM5 Wireless Noise Canceling Headphones (Platinum Silver)',
    merchantName: 'Bic Camera Tokyo Direct · Tax-Free Exempt',
    stickerPrice: 49500,
    stickerCurrency: 'JPY',
    trueCost: 5184500,
    targetCurrency: 'IDR',
    bnplBreakdown: {
      tenorMonths: 3,
      nominalApr: 0.12,
      effectiveAnnualRate: 0.214,
      totalFinanceCharge: 195000,
      isPredatory: false,
    },
    landedCostBreakdown: {
      spotFxRate: 105,
      effectiveFxRate: 107.6,
      fxMarkupCost: 128700,
      totalCustomsTaxes: 330000,
      touristTaxRefund: 471700,
    },
    optimalStopping: {
      decision: 'BUY',
      reservationPrice: 5450000,
      percentileRank: 11.2,
      daysLeft: 8,
      rationale:
        'Favorable JPY exchange rate puts the total cost well below your target price, and it qualifies for the $500 USD personal baggage tax-free allowance.',
    },
  },
];

const FRIENDLY_TIPS = [
  {
    icon: '',
    text: 'Friendly tip: Waiting 3 days on your laptop saves Rp 1.50M!',
    mood: 'Stress-Free',
    sub: "You're doing great — Rp 2.75M saved on bills this week.",
  },
  {
    icon: '',
    text: 'All virtual cards are shielded from hidden installment fees.',
    mood: 'Protected',
    sub: 'Your budget is right on track with safe funds ready in checking.',
  },
  {
    icon: '',
    text: 'Airport tourist tax refund adds Rp 1.68M back to your travel pot!',
    mood: 'Smart Saver',
    sub: '84% of your monthly savings goal is already locked in.',
  },
];

export function App() {
  const [keyPair, setKeyPair] = useState<UserKeyPair | null>(null);
  const [checkingBalance, setCheckingBalance] = useState(25000000);
  const [potBalance, setPotBalance] = useState(18500000);
  const [transactions, setTransactions] = useState<any[]>([]);
  const [executedOrders, setExecutedOrders] = useState<any[]>([]);
  const [disposableCards, setDisposableCards] = useState<any[]>([]);

  // Navigation & Autonomy state (controlled by MorphingBottomDock)
  const [activeSection, setActiveSection] = useState<NavSection>('all');
  const [autonomyTier, setAutonomyTier] = useState<AgentAutonomyTier>('tier2_online');
  const [activeScenario, setActiveScenario] = useState<ProductScenario>(PRODUCT_SCENARIOS[0]);

  // Active Mandate state
  const [activeMandate, setActiveMandate] = useState<any | null>(null);
  const [isMandateModalOpen, setIsMandateModalOpen] = useState(false);

  // Scam intervention state
  const [isScamModalOpen, setIsScamModalOpen] = useState(false);
  const [scamReasons, setScamReasons] = useState<string[]>([]);
  const [scamZScore, setScamZScore] = useState(0);

  // Execution state
  const [isExecuting, setIsExecuting] = useState(false);
  const [isSettled, setIsSettled] = useState(false);
  const [isOnboardingOpen, setIsOnboardingOpen] = useState(true);

  // Friendly greeting & Settings state
  const [friendlyTipIdx, setFriendlyTipIdx] = useState(0);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isExported, setIsExported] = useState(false);

  // Multi-Currency preference
  const [userBaseCurrency, setUserBaseCurrency] = useState<string>(
    () => localStorage.getItem('tc_user_currency') || 'AUD'
  );

  const handleCurrencyChange = (curr: string) => {
    setUserBaseCurrency(curr);
    localStorage.setItem('tc_user_currency', curr);
  };

  // User Location & Nearest Store Hub state
  const [userLocation, setUserLocation] = useState<string>(
    () => localStorage.getItem('tc_user_location') || 'tokyo'
  );
  const [isLocationModalOpen, setIsLocationModalOpen] = useState(false);
  const [gpsStatus, setGpsStatus] = useState<string | null>(null);

  // Fresh user empty state ("You haven't ... yet")
  const [isFreshUser, setIsFreshUser] = useState<boolean>(
    () => localStorage.getItem('tc_is_fresh') === 'true'
  );

  const activeHub = LOCATION_HUBS[userLocation] || LOCATION_HUBS.tokyo;

  const handleLocationSelect = (hubId: string, syncCurrency: boolean = true) => {
    setUserLocation(hubId);
    localStorage.setItem('tc_user_location', hubId);
    if (syncCurrency && LOCATION_HUBS[hubId]?.currency) {
      handleCurrencyChange(LOCATION_HUBS[hubId].currency);
    }
    setIsLocationModalOpen(false);
  };

  const handleDetectGpsLocation = () => {
    setGpsStatus('Acquiring GPS fix...');
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const userLat = pos.coords.latitude;
          const userLon = pos.coords.longitude;
          let closestKey = 'tokyo';
          let minDistance = Infinity;

          for (const [key, hub] of Object.entries(LOCATION_HUBS)) {
            const d = Math.hypot(hub.lat - userLat, hub.lon - userLon);
            if (d < minDistance) {
              minDistance = d;
              closestKey = key;
            }
          }
          setGpsStatus(`Located near ${LOCATION_HUBS[closestKey].city}!`);
          setTimeout(() => {
            handleLocationSelect(closestKey, true);
            setGpsStatus(null);
          }, 600);
        },
        () => {
          setGpsStatus('Defaulted to Tokyo Hub');
          setTimeout(() => {
            handleLocationSelect('tokyo', true);
            setGpsStatus(null);
          }, 600);
        },
        { timeout: 4000 }
      );
    } else {
      handleLocationSelect('tokyo', true);
      setGpsStatus(null);
    }
  };

  const handleToggleFreshUser = () => {
    setIsFreshUser((prev) => {
      const next = !prev;
      localStorage.setItem('tc_is_fresh', next ? 'true' : 'false');
      return next;
    });
  };

  const handleActivateFreshSample = (scenarioId: string) => {
    setIsFreshUser(false);
    localStorage.setItem('tc_is_fresh', 'false');
    const sc = PRODUCT_SCENARIOS.find((s) => s.id === scenarioId);
    if (sc) setActiveScenario(sc);
  };

  const hour = new Date().getHours();
  const timeGreeting =
    hour < 12 ? 'Good morning' : hour >= 18 ? 'Good evening' : 'Good afternoon';
  const currentTip = FRIENDLY_TIPS[friendlyTipIdx];

  useEffect(() => {
    const kp = getOrCreateUserKeyPair();
    setKeyPair(kp);
    fetchBankState();
  }, []);

  const fetchBankState = async () => {
    try {
      const [accRes, txRes] = await Promise.all([
        fetch('/api/bank/accounts'),
        fetch('/api/bank/transactions'),
      ]);

      if (accRes.ok) {
        const accData = await accRes.json();
        const checking = accData.accounts.find((a: any) => a.account_id === 'ACC_USER_CHECKING');
        const pot = accData.accounts.find((a: any) => a.account_id === 'ACC_USER_SINKING_POT');
        if (checking) setCheckingBalance(checking.balance);
        if (pot) setPotBalance(pot.balance);
      }

      if (txRes.ok) {
        const txData = await txRes.json();
        setTransactions(txData.transactions || []);
        setExecutedOrders(txData.executed_orders || []);
        setDisposableCards(txData.disposable_cards || []);
      }
    } catch {
      // Offline fallback for demo UI
    }
  };

  const handleDownloadActivityReceipt = () => {
    const payload = {
      exported_at: new Date().toISOString(),
      user_public_key: keyPair?.publicKeyHex || 'ed25519-local',
      autonomy_tier: autonomyTier,
      balances: {
        checking_idr: checkingBalance,
        sinking_pot_idr: potBalance,
      },
      active_mandate: activeMandate,
      transactions,
      disposable_cards: disposableCards,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `truecost-activity-receipt-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    setIsExported(true);
    setTimeout(() => setIsExported(false), 2500);
  };

  const handleMandateCreated = (mandate: any, bankResponse: any) => {
    setActiveMandate(mandate);
    if (bankResponse?.pot_balance !== undefined) setPotBalance(bankResponse.pot_balance);
    if (bankResponse?.checking_balance !== undefined)
      setCheckingBalance(bankResponse.checking_balance);
    setTransactions((prev) => [
      ...prev,
      {
        type: 'RESERVE_SINKING_POT',
        amount: mandate.max_budget,
        currency: 'IDR',
        reason: `Signed Ed25519 Intent Mandate (${mandate.mandate_id})`,
        timestamp: new Date().toISOString(),
      },
    ]);
    fetchBankState();
  };

  const handleExecuteCompliantPurchase = async () => {
    if (!keyPair) return;
    if (autonomyTier === 'tier0_invisible') {
      alert(
        'Tier 0 Read-Only Mode is active in the Bottom Dock. Switch to Tier 2 Autonomous to execute purchases.'
      );
      return;
    }
    if (autonomyTier === 'tier3_dnd') {
      handleTriggerScamSimulation();
      return;
    }

    setIsExecuting(true);

    try {
      let computedLandedCost = activeScenario.trueCost;
      try {
        const landedRes = await fetch('/api/quant/landed-cost', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            item_price_foreign: activeScenario.stickerPrice,
            foreign_currency: activeScenario.stickerCurrency,
            target_currency: activeScenario.targetCurrency,
            fx_spot_rate: activeScenario.landedCostBreakdown.spotFxRate,
            fx_spread_percent: 0.025,
            has_npwp: true,
            is_tourist_refund_eligible: true,
          }),
        });
        if (landedRes.ok) {
          const landedData = await landedRes.json();
          if (landedData.final_landed_cost) computedLandedCost = landedData.final_landed_cost;
        }
      } catch {
        // Fallback to deterministic scenario value
      }

      const agentKey = nacl.sign.keyPair();
      const agentPubHex = toHexString(agentKey.publicKey);

      const cartId = `CART-${Date.now().toString(36).toUpperCase()}`;
      const cartPayload = {
        cart_id: cartId,
        intent_mandate_id: activeMandate ? activeMandate.mandate_id : 'MANDATE-DEFAULT-DEMO',
        merchant_id: 'VERIFIED_MERCHANT',
        merchant_name: activeScenario.merchantName,
        item_title: activeScenario.itemTitle,
        sticker_price: activeScenario.stickerPrice,
        currency: 'IDR',
        landed_cost: computedLandedCost,
        payment_method: 'DEBIT',
        effective_apr: 0.0,
        scam_score: 0.05,
        created_at: new Date().toISOString(),
        agent_public_key: agentPubHex,
      };

      const canonicalData: Record<string, any> = {
        cart_id: cartPayload.cart_id,
        intent_mandate_id: cartPayload.intent_mandate_id,
        merchant_id: cartPayload.merchant_id,
        merchant_name: cartPayload.merchant_name,
        item_title: cartPayload.item_title,
        sticker_price: Number(cartPayload.sticker_price),
        currency: cartPayload.currency,
        landed_cost: Number(cartPayload.landed_cost),
        payment_method: cartPayload.payment_method,
        effective_apr: Number(cartPayload.effective_apr),
        scam_score: Number(cartPayload.scam_score),
        created_at: cartPayload.created_at,
        agent_public_key: cartPayload.agent_public_key,
      };

      const sortedObj: Record<string, any> = {};
      Object.keys(canonicalData)
        .sort()
        .forEach((k) => {
          sortedObj[k] = canonicalData[k];
        });
      const canonicalBytes = new TextEncoder().encode(JSON.stringify(sortedObj));
      const sig = nacl.sign.detached(canonicalBytes, agentKey.secretKey);
      const signedCart = {
        ...cartPayload,
        agent_signature: toHexString(sig),
      };

      let settledOnBackend = false;
      if (activeMandate) {
        try {
          const bankRes = await fetch('/api/bank/execute-cart', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cart: signedCart }),
          });

          if (bankRes.ok) {
            settledOnBackend = true;
            setIsSettled(true);
            await fetchBankState();
          }
        } catch {
          // Fallback to real-flow below
        }
      }

      if (!settledOnBackend) {
        try {
          const priceAud = Number((computedLandedCost / 10400).toFixed(2));
          const taxRefundAud = Number(
            (activeScenario.landedCostBreakdown.touristTaxRefund / 10400).toFixed(2)
          );

          const realFlowRes = await fetch('/api/bank/real-flow', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              item_name: activeScenario.itemTitle,
              merchant_name: activeScenario.merchantName,
              amount_aud: Math.max(10, priceAud),
              tax_refund_aud: taxRefundAud,
              step: 'reserve_and_settle',
            }),
          });

          if (realFlowRes.ok) {
            settledOnBackend = true;
            setIsSettled(true);
            await fetchBankState();
          }
        } catch {
          // Offline fallback below
        }
      }

      if (!settledOnBackend) {
        setIsSettled(true);
        setPotBalance((prev) => Math.max(0, prev - computedLandedCost));
        setDisposableCards((prev) => [
          ...prev,
          {
            masked_pan: `4532 •••• •••• ${Math.floor(1000 + Math.random() * 9000)}`,
            spending_limit: computedLandedCost,
            currency: 'IDR',
            status: 'BURNED (SETTLED)',
          },
        ]);
        setTransactions((prev) => [
          ...prev,
          {
            type: 'PURCHASE_SETTLEMENT',
            amount: computedLandedCost,
            currency: 'IDR',
            reason: `Settled ${activeScenario.badge} via Cart Mandate ${cartId}`,
            timestamp: new Date().toISOString(),
          },
        ]);
      }
    } finally {
      setIsExecuting(false);
    }
  };

  const handleTriggerScamSimulation = async () => {
    try {
      const res = await fetch('/api/quant/scam-check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          listing_price: 3990000.0,
          market_prices: [16000000, 16800000, 17200000, 17500000, 18500000],
          seller_feedback_score: 55.0,
          seller_review_count: 2,
          seller_account_age_days: 5,
          listing_url: 'https://tokopedia-flash-sale-promo.xyz/deal',
          demands_off_platform_payment: true,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setScamZScore(data.modified_z_score);
        setScamReasons(data.reasons);
        setIsScamModalOpen(true);
        return;
      }
    } catch {
      // Offline deterministic fallback
    }

    setScamZScore(-11.42);
    setScamReasons([
      'Suspiciously low price: 76.8% below the normal Rp 17.2M retail price',
      'Off-platform payment coercion detected (WhatsApp/direct transfer requested)',
      'Unverified new seller account (5 days old, 2 reviews)',
    ]);
    setIsScamModalOpen(true);
  };

  return (
    <div className="min-h-screen muestra-mesh-bg text-[#141726] flex flex-col pb-32 selection:bg-[#2B44E8] selection:text-white">
      <Navbar
        checkingBalance={checkingBalance}
        potBalance={potBalance}
        userPublicKey={keyPair ? keyPair.publicKeyHex : '...'}
        autonomyTier={autonomyTier}
        onOpenMandateModal={() => setIsMandateModalOpen(true)}
        onOpenSettings={() => setIsSettingsOpen(true)}
        userBaseCurrency={userBaseCurrency}
        onCurrencyChange={handleCurrencyChange}
        userLocation={userLocation}
        onOpenLocationModal={() => setIsLocationModalOpen(true)}
        isFreshUser={isFreshUser}
        onToggleFreshUser={handleToggleFreshUser}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-3 pb-10 space-y-6">
        {/* ROW 1 (OPTION A): Asymmetric Interlocking Greeting Squircle + Vertical 3D Thermometer Goal Gauge */}
        <section className="grid grid-cols-1 md:grid-cols-12 gap-4 items-stretch">
          {/* Left 8 Cols: Friendly Greeting & Weekly Savings Squircle */}
          <div className="md:col-span-8 soma-glass rounded-[32px] p-5 flex flex-col justify-between gap-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-3">
                <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-[#EB7951] via-[#EABAA8] to-[#FDF6E4] border border-white flex items-center justify-center font-bold text-sm text-[#141726] shadow-xs shrink-0">
                  R
                </div>
                <div>
                  <h2 className="text-base sm:text-lg font-extrabold text-[#141726] tracking-tight">
                    {timeGreeting}, Rafif!
                  </h2>
                  <p className="text-xs text-[#5A5E72]">{currentTip.sub}</p>
                </div>
              </div>
              <button
                onClick={() => setFriendlyTipIdx((prev) => (prev + 1) % FRIENDLY_TIPS.length)}
                className="px-3 py-1 rounded-full bg-[#10B981]/12 border border-[#10B981]/25 text-[#065F46] text-xs font-mono font-bold hover:bg-[#10B981]/20 transition"
              >
                {currentTip.mood}
              </button>
            </div>

            <div className="flex flex-wrap items-end justify-between gap-3 pt-1">
              <div>
                <div className="text-3xl font-black font-mono tracking-tight text-[#141726] leading-none">
                  {formatIdrInCurrency(2750000, userBaseCurrency)}
                </div>
                <span className="text-xs font-semibold text-[#5A5E72]">
                  Saved on bills &amp; hidden fees this week
                </span>
              </div>

              <button
                onClick={() => setFriendlyTipIdx((prev) => (prev + 1) % FRIENDLY_TIPS.length)}
                className="px-4 py-2 rounded-2xl bg-white/85 hover:bg-white border border-[#141726]/8 flex items-center gap-2 text-left transition shadow-2xs"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-[#2B44E8] shrink-0" />
                <span className="text-xs font-medium text-[#141726]">{currentTip.text}</span>
              </button>
            </div>
          </div>

          {/* Right 4 Cols: Option A Vertical 3D Thermometer Goal Squircle */}
          <div
            onClick={() => setFriendlyTipIdx((prev) => (prev + 1) % FRIENDLY_TIPS.length)}
            className="md:col-span-4 rounded-[32px] thermometer-squircle p-5 flex items-center justify-around gap-4 cursor-pointer"
          >
            <div className="flex flex-col items-center">
              <div className="thermometer-tube">
                <div className="thermometer-fill" />
              </div>
              <div className="thermometer-bulb" />
            </div>
            <div className="text-right">
              <span className="text-[11px] font-mono uppercase tracking-wider text-[#5A5E72] font-bold">
                Monthly Target
              </span>
              <div className="text-4xl font-black font-mono text-[#141726] leading-none mt-1">
                84%
              </div>
              <div className="text-sm font-bold text-[#141726] mt-0.5">Savings Goal</div>
              <span className="inline-block text-[11px] font-mono text-[#2B44E8] font-bold mt-1">
                On Track
              </span>
            </div>
          </div>
        </section>

        {/* Nearest Verified Store & Tourist Tax-Exemption Bar */}
        {activeHub && (
          <section className="p-4 sm:p-5 rounded-[26px] soma-glass border border-white/80 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-10 h-10 rounded-2xl bg-[#2B44E8]/10 text-[#2B44E8] flex items-center justify-center font-bold text-sm shrink-0 font-mono">
                {activeHub.flag}
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-[#141726] truncate">
                    Nearest Store: {activeHub.storeName}
                  </span>
                  <span className="text-[10px] font-mono text-[#5A5E72] whitespace-nowrap">
                    · {activeHub.distance}
                  </span>
                  <span className="px-2 py-0.5 rounded-full bg-[#10B981]/15 text-[#065F46] text-[9px] font-mono font-bold whitespace-nowrap">
                    {activeHub.badge}
                  </span>
                </div>
                <p className="text-[11px] text-[#5A5E72] truncate">
                  {activeHub.ruleTitle} — {activeHub.ruleDesc}
                </p>
              </div>
            </div>
            <button
              onClick={() => setIsLocationModalOpen(true)}
              className="px-3.5 py-1.5 rounded-full bg-white/90 hover:bg-white border border-black/8 text-[11px] font-semibold text-[#2B44E8] flex items-center justify-center gap-1.5 self-start md:self-auto transition shadow-2xs shrink-0 cursor-pointer"
            >
              <MapPin className="w-3.5 h-3.5 text-[#2B44E8]" />
              <span>Change Hub ({activeHub.city})</span>
            </button>
          </section>
        )}

        {/* Fresh User Empty State ("You haven't searched or scanned a bill yet") */}
        {isFreshUser && (
          <section className="p-6 sm:p-8 rounded-[32px] soma-glass text-center space-y-4 border border-[#2B44E8]/20 shadow-sm relative overflow-hidden">
            <div className="w-14 h-14 mx-auto rounded-3xl bg-[#2B44E8]/10 text-[#2B44E8] flex items-center justify-center">
              <Sparkles className="w-7 h-7 text-[#2B44E8]" />
            </div>
            <div className="max-w-md mx-auto space-y-1.5">
              <h3 className="text-lg sm:text-xl font-extrabold text-[#141726] tracking-tight">
                You haven&apos;t searched or scanned a bill yet
              </h3>
              <p className="text-xs text-[#5A5E72] leading-relaxed">
                Paste any product listing, marketplace link, or scan an airport duty-free receipt below.
                Autopilot calculates your true landed cost, strips hidden installment fees, and verifies seller safety.
              </p>
            </div>

            <div className="pt-2">
              <div className="text-[10px] font-mono uppercase tracking-wider text-[#8E8A84] font-bold mb-3">
                Try a quick-start real bill:
              </div>
              <div className="flex flex-wrap items-center justify-center gap-2 max-w-xl mx-auto">
                <button
                  onClick={() => handleActivateFreshSample('thinkpad_au')}
                  className="px-4 py-2 rounded-2xl bg-white hover:bg-white/80 border border-black/8 text-xs font-semibold text-[#141726] transition shadow-2xs flex items-center gap-1.5 cursor-pointer"
                >
                  <span>💻</span>
                  <span>ThinkPad T14s · Save $270</span>
                </button>
                <button
                  onClick={() => handleActivateFreshSample('macbook_sg')}
                  className="px-4 py-2 rounded-2xl bg-white hover:bg-white/80 border border-black/8 text-xs font-semibold text-[#141726] transition shadow-2xs flex items-center gap-1.5 cursor-pointer"
                >
                  <span>🍏</span>
                  <span>MacBook Air · Fee Check</span>
                </button>
                <button
                  onClick={() => handleActivateFreshSample('sony_jp')}
                  className="px-4 py-2 rounded-2xl bg-white hover:bg-white/80 border border-black/8 text-xs font-semibold text-[#141726] transition shadow-2xs flex items-center gap-1.5 cursor-pointer"
                >
                  <span>🎧</span>
                  <span>Sony XM5 · Tax-Free JPY</span>
                </button>
                <button
                  onClick={handleTriggerScamSimulation}
                  className="px-4 py-2 rounded-2xl bg-[#EB7951]/10 hover:bg-[#EB7951]/15 border border-[#EB7951]/25 text-xs font-semibold text-[#EB7951] transition shadow-2xs flex items-center gap-1.5 cursor-pointer"
                >
                  <span>🛡️</span>
                  <span>Test Scam Shield</span>
                </button>
              </div>
            </div>
          </section>
        )}

        {/* ROW 2 (OPTION A + C): L-Shaped Hero Card with Circular Cutout Notch + Staggered FX Radar & Coral Alert */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
          {/* Left 7 Cols: L-Shaped Smoked Frosted Glass Hero Card with Bottom-Right Concave Scan Orb Cutout */}
          <div className="lg:col-span-7 relative flex flex-col">
            <div className="flex-1 frosted-glass-insight hero-cutout-card p-6 sm:p-8 text-white relative overflow-hidden flex flex-col justify-between min-h-[290px]">
              {/* Diffused Muestra-64 Glowing Orb + Fine White Geometric Arcs */}
              <div className="absolute -right-10 -top-10 w-72 h-72 rounded-full muestra-hero-orb opacity-90 pointer-events-none" />
              <div className="absolute right-8 top-6 w-56 h-56 rounded-full border border-white/15 pointer-events-none" />

              <div className="relative z-10 flex items-center justify-between gap-2">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full frosted-inner-row text-[11px] font-mono uppercase tracking-wider text-[#FDF6E4]">
                  <ShieldCheck className="w-3.5 h-3.5 text-[#EB7951]" />
                  Safe Balance
                </div>
                <span className="text-xs font-mono text-[#EABAA8]">
                  60d Buffer Protected (+Rp 10.0M)
                </span>
              </div>

              <div className="relative z-10 my-3">
                <div className="text-3xl sm:text-5xl font-black font-mono tracking-tight text-white">
                  {formatIdrInCurrency(checkingBalance, userBaseCurrency)}
                </div>
                <p className="text-xs sm:text-sm text-[#EABAA8] font-mono mt-1">
                  ≈ Rp {checkingBalance.toLocaleString('id-ID')} · Escrow Pot: {formatIdrInCurrency(potBalance, userBaseCurrency)}
                </p>
              </div>

              <div className="relative z-10 my-2 p-4 rounded-[22px] frosted-inner-well max-w-lg mr-24">
                <p className="text-xs sm:text-sm text-white/90 leading-relaxed">
                  Uncovers hidden installment fees, calculates cross-border import duties &amp; airport tax refunds, and settles automatically inside your signed budget.
                </p>
              </div>

              {/* Bottom Capsule Action Bar (Offset left of the 112px circular cutout notch) */}
              <div className="relative z-10 flex flex-wrap items-center gap-3 pt-1 pr-28">
                <button
                  onClick={() => setIsMandateModalOpen(true)}
                  className="pl-5 pr-2 py-2 rounded-full frosted-inner-row hover:bg-white/20 text-white text-xs font-semibold flex items-center gap-3 transition group"
                >
                  <KeyRound className="w-3.5 h-3.5 text-[#EABAA8]" />
                  <span>
                    {activeMandate
                      ? `Mandate Signed (${activeMandate.mandate_id})`
                      : 'Set Protected Spending Cap'}
                  </span>
                  <span className="w-8 h-8 rounded-full bg-white text-[#141726] flex items-center justify-center group-hover:translate-x-0.5 transition-transform">
                    <ArrowRight className="w-4 h-4" />
                  </span>
                </button>
              </div>
            </div>

            {/* Concave Circular Cutout Socket in Bottom-Right Corner with 3D Scan Bill Orb */}
            <div className="scan-orb-socket">
              <button
                onClick={() => setIsMandateModalOpen(true)}
                className="scan-orb-btn transition-transform hover:scale-105 active:scale-95"
                title="Configure Protected Budget or Scan Bill"
              >
                <Sparkles className="w-6 h-6 text-white" />
                <span className="text-[11px] font-extrabold tracking-tight mt-0.5">Scan Bill</span>
              </button>
            </div>
          </div>

          {/* Right 5 Cols: Option A + C Staggered Bento (Circular FX Radar Dial + Terracotta Coral Fee Alert + View Switcher) */}
          <div className="lg:col-span-5 grid grid-cols-1 sm:grid-cols-2 gap-4 items-stretch">
            {/* Top-Left of Right Bento: Option A Circular Smoked-Glass FX Radar Dial */}
            <div className="fx-radar-circle p-5 text-white">
              <div className="w-full h-full rounded-full border border-white/15 flex flex-col items-center justify-center relative p-3 text-center">
                <div className="absolute inset-2.5 rounded-full border border-dashed border-white/20 pointer-events-none" />
                <span className="w-2.5 h-2.5 rounded-full bg-[#EB7951] shadow-[0_0_10px_#EB7951] mb-1.5" />
                <span className="text-[10px] font-mono uppercase tracking-widest text-white/75">
                  {userBaseCurrency === 'IDR' ? 'IDR · AUD' : `${userBaseCurrency} · IDR`}
                </span>
                <span className="text-2xl font-black font-mono tracking-tight text-white mt-0.5">
                  {userBaseCurrency === 'IDR'
                    ? '10,400'
                    : Math.round(FX_TO_IDR[userBaseCurrency] || 10400).toLocaleString()}
                </span>
                <span className="text-[10px] font-mono text-[#10B981] font-bold mt-1">
                  {activeScenario.optimalStopping.decision === 'WAIT'
                    ? `● Wait ${activeScenario.optimalStopping.daysLeft}d`
                    : '● Best Buy Window'}
                </span>
              </div>
            </div>

            {/* Top-Right of Right Bento: Option C Terracotta Coral Frosted "Fee Alert" Square */}
            <div className="rounded-[30px] coral-frosted-tile p-5 text-white flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono uppercase tracking-wider font-bold text-white/90">
                  Fee Alert
                </span>
                <span className="px-2 py-0.5 rounded-full bg-white/20 text-[10px] font-mono font-bold">
                  {activeScenario.bnplBreakdown.totalFinanceCharge > 0 ? 'Tier 2' : 'Tier 1'}
                </span>
              </div>
              <div className="my-2">
                <div className="text-2xl font-black font-mono">
                  {activeScenario.bnplBreakdown.totalFinanceCharge > 0
                    ? `+Rp ${Math.round(activeScenario.bnplBreakdown.totalFinanceCharge / 1000).toLocaleString()}k`
                    : 'Rp 0 Fees'}
                </div>
                <p className="text-xs text-white/95 leading-snug mt-1">
                  {activeScenario.bnplBreakdown.totalFinanceCharge > 0
                    ? 'Hidden monthly account fees uncovered on “0% promo” installment plans.'
                    : 'Zero hidden installment fees detected on this direct checkout.'}
                </p>
              </div>
              <span className="text-[10px] font-mono text-white/85">
                {activeScenario.bnplBreakdown.totalFinanceCharge > 0
                  ? 'Auto-switched to direct debit'
                  : 'Verified clean direct debit'}
              </span>
            </div>

            {/* Bottom Span of Right Bento: Perforated Ticket-Stub Protection Bar */}
            <div className="sm:col-span-2 rounded-[26px] soma-glass p-4 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <Layers className="w-4 h-4 text-[#2B44E8]" />
                <div className="text-xs">
                  <span className="text-[#5A5E72] font-mono">Workspace View: </span>
                  <strong className="text-[#141726] font-mono uppercase">{activeSection}</strong>
                </div>
              </div>
              {activeSection !== 'all' ? (
                <button
                  onClick={() => setActiveSection('all')}
                  className="text-xs font-mono text-[#2B44E8] font-bold hover:underline flex items-center gap-1"
                >
                  <Sparkles className="w-3.5 h-3.5" /> Show All
                </button>
              ) : (
                <span className="text-[11px] font-mono font-bold text-[#10B981]">
                  ● Autonomous Guardrails Active
                </span>
              )}
            </div>
          </div>
        </section>

        {/* Section 1: The One Number Reveal (Pre-Purchase Financial Comparison) */}
        {(activeSection === 'all' || activeSection === 'copilot') && (
          <section className="space-y-3 animate-in fade-in duration-300">
            {isFreshUser && activeSection === 'copilot' ? (
              <div className="p-8 rounded-[32px] soma-glass text-center space-y-3 border border-black/8">
                <div className="w-12 h-12 mx-auto rounded-2xl bg-[#2B44E8]/10 text-[#2B44E8] flex items-center justify-center font-bold">
                  <Sparkles className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-bold text-[#141726]">No price or fee breakdown yet</h3>
                <p className="text-xs text-[#5A5E72] max-w-sm mx-auto">
                  Search for an item or scan a receipt on Home to uncover true delivered cost, import taxes, and installment fees.
                </p>
                <button
                  onClick={() => handleActivateFreshSample('thinkpad_au')}
                  className="px-4 py-2 rounded-full bg-[#131522] text-white text-xs font-bold transition shadow-xs hover:bg-black cursor-pointer"
                >
                  Load Sample Price Check
                </button>
              </div>
            ) : (
              <OneNumberCard
                itemTitle={activeScenario.itemTitle}
                merchantName={activeScenario.merchantName}
                stickerPrice={activeScenario.stickerPrice}
                stickerCurrency={activeScenario.stickerCurrency}
                trueCost={activeScenario.trueCost}
                targetCurrency={activeScenario.targetCurrency}
                bnplBreakdown={activeScenario.bnplBreakdown}
                landedCostBreakdown={activeScenario.landedCostBreakdown}
                optimalStopping={activeScenario.optimalStopping}
                onExecutePurchase={handleExecuteCompliantPurchase}
                isExecuting={isExecuting}
                isSettled={isSettled}
                scenarios={PRODUCT_SCENARIOS}
                activeScenarioId={activeScenario.id}
                userBaseCurrency={userBaseCurrency}
                onSelectScenario={(sc) => {
                  setActiveScenario(sc);
                  setIsSettled(false);
                }}
                onScamDetected={(reasons, zScore) => {
                  setScamZScore(zScore);
                  setScamReasons(reasons);
                  setIsScamModalOpen(true);
                }}
              />
            )}
          </section>
        )}

        {/* Section 2: Time-Travel Replay Simulator & Benchmarking */}
        {(activeSection === 'all' || activeSection === 'replay') && (
          <section className="animate-in fade-in duration-300">
            {isFreshUser && activeSection === 'replay' ? (
              <div className="p-8 rounded-[32px] soma-glass text-center space-y-3 border border-black/8">
                <div className="w-12 h-12 mx-auto rounded-2xl bg-[#10B981]/10 text-[#10B981] flex items-center justify-center font-bold">
                  <ShieldCheck className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-bold text-[#141726]">Scam Shield is standing by</h3>
                <p className="text-xs text-[#5A5E72] max-w-sm mx-auto">
                  You haven&apos;t analyzed any seller links yet. Paste any marketplace listing or chat offer to verify seller authenticity.
                </p>
                <button
                  onClick={handleTriggerScamSimulation}
                  className="px-4 py-2 rounded-full bg-[#EB7951] text-white text-xs font-bold transition shadow-xs hover:bg-[#d96740] cursor-pointer"
                >
                  Simulate Scam Outlier Detection
                </button>
              </div>
            ) : (
              <ReplaySimulator />
            )}
          </section>
        )}

        {/* Section 3: Immutable Audit & Banking Trail */}
        {(activeSection === 'all' || activeSection === 'vault') && (
          <section className="animate-in fade-in duration-300">
            {isFreshUser && activeSection === 'vault' ? (
              <div className="p-8 rounded-[32px] soma-glass text-center space-y-3 border border-black/8">
                <div className="w-12 h-12 mx-auto rounded-2xl bg-[#2B44E8]/10 text-[#2B44E8] flex items-center justify-center font-bold">
                  <KeyRound className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-bold text-[#141726]">You haven&apos;t created any purchase mandates yet</h3>
                <p className="text-xs text-[#5A5E72] max-w-sm mx-auto">
                  Set a cryptographic spending cap to allow TrueCost Autopilot to lock escrow and safely settle verified deals.
                </p>
                <button
                  onClick={() => setIsMandateModalOpen(true)}
                  className="px-4 py-2 rounded-full bg-[#131522] text-white text-xs font-bold transition shadow-xs hover:bg-black cursor-pointer"
                >
                  Create Your First Mandate
                </button>
              </div>
            ) : (
              <AuditTrailView
                transactions={transactions}
                executedOrders={executedOrders}
                disposableCards={disposableCards}
                checkingBalance={checkingBalance}
                potBalance={potBalance}
                userPublicKey={keyPair ? keyPair.publicKeyHex : '...'}
                onOpenMandateModal={() => setIsMandateModalOpen(true)}
              />
            )}
          </section>
        )}
      </main>

      {/* THE OVERHAULED MORPHING FLOATING BOTTOM DOCK (Hidden while in 4-Page Get Started Onboarding) */}
      {!isOnboardingOpen && (
        <MorphingBottomDock
          activeSection={activeSection}
          onSelectSection={setActiveSection}
          autonomyTier={autonomyTier}
          onSelectAutonomyTier={setAutonomyTier}
          checkingBalance={checkingBalance}
          potBalance={potBalance}
          activeMandate={activeMandate}
          onOpenMandateModal={() => setIsMandateModalOpen(true)}
          onTriggerScamSimulation={handleTriggerScamSimulation}
          transactionsCount={transactions.length}
        />
      )}


      {/* Modals */}
      {keyPair && (
        <MandateModal
          isOpen={isMandateModalOpen}
          onClose={() => setIsMandateModalOpen(false)}
          keyPair={keyPair}
          onMandateCreated={handleMandateCreated}
        />
      )}

      {/* Settings & Activity Receipt Download Modal */}
      {isSettingsOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#131522]/60 backdrop-blur-md animate-in fade-in duration-200">
          <div className="max-w-lg w-full rounded-[32px] soma-glass p-6 space-y-4 border border-white shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-[#141726]/10">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl muestra-hero-orb flex items-center justify-center text-white font-bold">
                  <Settings className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-base font-extrabold text-[#141726]">
                    TrueCost Settings
                  </h2>
                  <p className="text-xs text-[#5A5E72]">
                    Activity receipts, privacy &amp; preferences
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsSettingsOpen(false)}
                className="w-8 h-8 rounded-full bg-white/80 hover:bg-white flex items-center justify-center text-[#141726] border border-black/8"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Profile & Preferences */}
            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between p-3 rounded-2xl bg-white/80 border border-black/6">
                <div>
                  <div className="font-bold text-[#141726]">Rafif · Verified Account</div>
                  <div className="text-[11px] text-[#5A5E72] font-mono">
                    On-Device Privacy Shield Active
                  </div>
                </div>
                <span className="px-2.5 py-1 rounded-full bg-[#10B981]/15 text-[#065F46] font-mono text-[10px] font-bold">
                  PROTECTED
                </span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-2xl bg-white/80 border border-black/6">
                <div>
                  <div className="font-semibold text-[#141726]">Home Currency &amp; Corridor</div>
                  <div className="text-[11px] text-[#5A5E72]">Active base for all conversions</div>
                </div>
                <span className="font-mono font-bold text-[#2B44E8]">
                  {userBaseCurrency} ↔ IDR ({userBaseCurrency === 'IDR' ? '1.0' : Math.round(FX_TO_IDR[userBaseCurrency] || 10400).toLocaleString()})
                </span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-2xl bg-white/80 border border-black/6">
                <div>
                  <div className="font-semibold text-[#141726]">Location Hub &amp; Store</div>
                  <div className="text-[11px] text-[#5A5E72]">{activeHub.city} · {activeHub.storeName}</div>
                </div>
                <button
                  onClick={() => {
                    setIsSettingsOpen(false);
                    setIsLocationModalOpen(true);
                  }}
                  className="px-2.5 py-1 rounded-full bg-[#2B44E8]/10 text-[#2B44E8] font-mono text-[10px] font-bold hover:bg-[#2B44E8]/20 transition"
                >
                  Change
                </button>
              </div>
              <div className="flex items-center justify-between p-3 rounded-2xl bg-white/80 border border-black/6">
                <div>
                  <div className="font-semibold text-[#141726]">Experience State</div>
                  <div className="text-[11px] text-[#5A5E72]">
                    {isFreshUser ? 'Fresh User Mode (First-Time Empty State)' : 'Active Analysis Mode'}
                  </div>
                </div>
                <button
                  onClick={handleToggleFreshUser}
                  className="px-2.5 py-1 rounded-full bg-black/5 hover:bg-black/10 text-[#141726] font-mono text-[10px] font-bold transition"
                >
                  {isFreshUser ? 'Switch to Active' : 'Switch to Fresh'}
                </button>
              </div>
            </div>

            {/* Frosted Glass Activity Receipt Download Card */}
            <div className="rounded-[26px] p-5 frosted-glass-summary text-white space-y-3 relative overflow-hidden">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-[#EABAA8]">
                  ACTIVITY &amp; RECEIPTS
                </span>
                <span className="text-[10px] font-mono px-2.5 py-0.5 rounded-full frosted-inner-row text-[#10B981]">
                  Verified JSON
                </span>
              </div>
              <div className="p-3.5 rounded-[18px] frosted-inner-well text-xs text-white/85 leading-relaxed">
                Download a complete copy of your verified price checks, protected budget caps, and account activity receipts for your personal records.
              </div>
              <button
                onClick={handleDownloadActivityReceipt}
                className="w-full p-2 pl-4 rounded-full frosted-action-pill text-white flex items-center justify-between transition active:scale-[0.99]"
              >
                <span className="text-xs font-bold">
                  {isExported ? 'Activity Receipt Downloaded!' : 'Download Activity Receipt'}
                </span>
                <span className="w-9 h-9 rounded-full bg-[#EB7951] text-white flex items-center justify-center">
                  {isExported ? <CheckCircle2 className="w-4 h-4" /> : <Download className="w-4 h-4" />}
                </span>
              </button>
            </div>

            <div className="flex items-center justify-between pt-2">
              <button
                onClick={() => {
                  setIsSettingsOpen(false);
                  setIsOnboardingOpen(true);
                }}
                className="text-xs font-semibold text-[#2B44E8] hover:underline"
              >
                Replay Welcome Guide
              </button>
              <button
                onClick={() => setIsSettingsOpen(false)}
                className="px-5 py-2 rounded-full bg-[#131522] text-white text-xs font-bold"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Location Hub Selector Modal */}
      {isLocationModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-[#F4F0EA] rounded-[32px] border border-white/80 max-w-md w-full p-6 shadow-2xl space-y-5 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-full bg-[#2B44E8]/10 text-[#2B44E8] flex items-center justify-center">
                  <MapPin className="w-5 h-5 text-[#2B44E8]" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-[#141726]">Your Location &amp; Store Hub</h3>
                  <p className="text-xs text-[#5A5E72]">Sets nearest store, customs &amp; tourist tax-free rules</p>
                </div>
              </div>
              <button
                onClick={() => setIsLocationModalOpen(false)}
                className="w-8 h-8 rounded-full bg-white/80 hover:bg-white text-[#141726] flex items-center justify-center transition border border-black/8 cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* GPS Auto Detect Button */}
            <button
              onClick={handleDetectGpsLocation}
              className="w-full py-2.5 px-4 rounded-2xl bg-[#2B44E8] hover:bg-[#1f35c4] text-white text-xs font-bold flex items-center justify-center gap-2 transition shadow-xs cursor-pointer"
            >
              <Compass className="w-4 h-4" />
              <span>{gpsStatus || 'Detect My Current Location (GPS Fix)'}</span>
            </button>

            {/* Hubs Grid */}
            <div className="space-y-2 max-h-[320px] overflow-y-auto pr-1">
              {Object.values(LOCATION_HUBS).map((hub) => {
                const isSelected = hub.id === userLocation;
                return (
                  <div
                    key={hub.id}
                    onClick={() => handleLocationSelect(hub.id, true)}
                    className={`p-3.5 rounded-2xl border transition cursor-pointer flex items-center justify-between ${
                      isSelected
                        ? 'bg-[#131522] text-white border-transparent shadow-md'
                        : 'bg-white hover:bg-white/80 text-[#141726] border-black/6'
                    }`}
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div
                        className={`w-9 h-9 rounded-xl flex items-center justify-center font-bold text-xs shrink-0 font-mono ${
                          isSelected ? 'bg-white/15 text-white' : 'bg-[#2B44E8]/10 text-[#2B44E8]'
                        }`}
                      >
                        {hub.flag}
                      </div>
                      <div className="min-w-0">
                        <div className="text-xs font-bold truncate">
                          {hub.city}, {hub.country}
                        </div>
                        <div className={`text-[11px] truncate ${isSelected ? 'text-white/70' : 'text-[#5A5E72]'}`}>
                          {hub.storeName} ({hub.distance})
                        </div>
                        <div
                          className={`text-[10px] font-mono font-semibold truncate ${
                            isSelected ? 'text-[#10B981]' : 'text-[#065F46]'
                          }`}
                        >
                          {hub.ruleTitle}
                        </div>
                      </div>
                    </div>
                    <div className="text-right shrink-0 ml-2">
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-[9px] font-mono font-bold ${
                          isSelected ? 'bg-[#10B981] text-white' : 'bg-black/5 text-[#5A5E72]'
                        }`}
                      >
                        {isSelected ? 'ACTIVE' : hub.currency}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="pt-2 border-t border-black/8 flex items-center justify-between text-xs text-[#5A5E72] font-mono">
              <span>Active Currency: <strong className="text-[#2B44E8]">{userBaseCurrency}</strong></span>
              <button
                onClick={() => setIsLocationModalOpen(false)}
                className="font-bold text-[#141726] hover:underline cursor-pointer"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}

      <ScamInterventionModal
        isOpen={isScamModalOpen}
        onClose={() => setIsScamModalOpen(false)}
        onOverrideConfirm={() => {
          setIsScamModalOpen(false);
          setTransactions((prev) => [
            ...prev,
            {
              type: 'TIER3_FRICTION_OVERRIDE',
              status: 'REJECTED_BY_BANK_POLICY',
              amount: 3990000,
              currency: 'IDR',
              reason: 'User completed 10s cooling-off attestation on suspicious listing',
              timestamp: new Date().toISOString(),
            },
          ]);
        }}
        scamReasons={scamReasons}
        modifiedZScore={scamZScore}
        listingPrice={3990000}
      />

      <OnboardingFlow
        isOpen={isOnboardingOpen}
        onClose={() => setIsOnboardingOpen(false)}
      />
    </div>
  );
}

export default App;


