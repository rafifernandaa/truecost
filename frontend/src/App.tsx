import { useState, useEffect } from 'react';
import nacl from 'tweetnacl';
import { Navbar } from './components/Navbar';
import { OneNumberCard } from './components/OneNumberCard';
import { ScamInterventionModal } from './components/ScamInterventionModal';
import { MandateModal } from './components/MandateModal';
import { AuditTrailView } from './components/AuditTrailView';
import { ReplaySimulator } from './components/ReplaySimulator';
import { getOrCreateUserKeyPair, type UserKeyPair, toHexString } from './lib/crypto';
import { ShieldCheck, ShieldAlert, KeyRound } from 'lucide-react';

export function App() {
  const [keyPair, setKeyPair] = useState<UserKeyPair | null>(null);
  const [checkingBalance, setCheckingBalance] = useState(25000000);
  const [potBalance, setPotBalance] = useState(0);
  const [transactions, setTransactions] = useState<any[]>([]);
  const [executedOrders, setExecutedOrders] = useState<any[]>([]);
  const [disposableCards, setDisposableCards] = useState<any[]>([]);

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

  // Load Keypair on mount
  useEffect(() => {
    const kp = getOrCreateUserKeyPair();
    setKeyPair(kp);
    fetchBankState();
  }, []);

  const fetchBankState = async () => {
    try {
      const [accRes, txRes] = await Promise.all([
        fetch('/api/bank/accounts'),
        fetch('/api/bank/transactions')
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

  const handleMandateCreated = (mandate: any, bankResponse: any) => {
    setActiveMandate(mandate);
    setPotBalance(bankResponse.pot_balance);
    setCheckingBalance(bankResponse.checking_balance);
    fetchBankState();
  };

  // Demo Case: Simulate Compliant Purchase Execution
  const handleExecuteCompliantPurchase = async () => {
    if (!keyPair) return;
    setIsExecuting(true);

    try {
      // 1. Fetch deterministic Landed Cost
      const landedRes = await fetch('/api/quant/landed-cost', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          item_price_foreign: 1580.0,
          foreign_currency: 'AUD',
          target_currency: 'IDR',
          fx_spot_rate: 10400.0,
          fx_spread_percent: 0.025,
          has_npwp: true,
          is_tourist_refund_eligible: true
        })
      });
      const landedData = await landedRes.json();

      // 2. Build Agent Cart Mandate
      const agentKey = nacl.sign.keyPair();
      const agentPubHex = toHexString(agentKey.publicKey);

      const cartId = `CART-${Date.now().toString(36).toUpperCase()}`;
      const cartPayload = {
        cart_id: cartId,
        intent_mandate_id: activeMandate ? activeMandate.mandate_id : 'MANDATE-DEFAULT-DEMO',
        merchant_id: 'LENOVO_AU',
        merchant_name: 'Lenovo Official Store Australia',
        item_title: 'Lenovo ThinkPad T14s Gen 4 (16GB RAM, 512GB SSD)',
        sticker_price: 1580.0,
        currency: 'IDR',
        landed_cost: landedData.final_landed_cost || 17582248.8,
        payment_method: 'DEBIT',
        effective_apr: 0.0,
        scam_score: 0.05,
        created_at: new Date().toISOString(),
        agent_public_key: agentPubHex
      };

      // 3. Agent signs Cart Mandate
      const canonicalData = {
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

      const sortedObj: any = {};
      Object.keys(canonicalData).sort().forEach(k => { sortedObj[k] = (canonicalData as any)[k]; });
      const canonicalBytes = new TextEncoder().encode(JSON.stringify(sortedObj));
      const sig = nacl.sign.detached(canonicalBytes, agentKey.secretKey);
      const signedCart = {
        ...cartPayload,
        agent_signature: toHexString(sig)
      };

      // 4. Submit to Core Bank Verifier
      const bankRes = await fetch('/api/bank/execute-cart', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cart: signedCart })
      });

      if (!bankRes.ok) {
        const err = await bankRes.json();
        alert(`Bank Policy Rejected: ${err.detail?.message || 'Policy violation'}`);
      } else {
        setIsSettled(true);
        fetchBankState();
      }
    } catch (err: any) {
      alert(`Execution error: ${err.message}`);
    } finally {
      setIsExecuting(false);
    }
  };

  // Demo Case: Simulate Scam Outlier Detection
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
          demands_off_platform_payment: true
        })
      });
      const data = await res.json();
      setScamZScore(data.modified_z_score);
      setScamReasons(data.reasons);
      setIsScamModalOpen(true);
    } catch (err: any) {
      alert(`Scam API error: ${err.message}`);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col font-sans selection:bg-zinc-800 selection:text-white">
      <Navbar
        checkingBalance={checkingBalance}
        potBalance={potBalance}
        userPublicKey={keyPair ? keyPair.publicKeyHex : '...'}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6 sm:space-y-8">
        {/* Hero & Quick Action Bar */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-5 p-5 sm:p-6 rounded-xl bg-zinc-900/40 border border-zinc-800">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-zinc-800/80 text-zinc-300 border border-zinc-700/80 text-[10px] font-mono tracking-wider uppercase">
              <ShieldCheck className="w-3.5 h-3.5 text-zinc-300" />
              Autonomous Financial Participant · AP2 Verifiable Mandates
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
              Pre-Purchase Financial Co-Pilot
            </h2>
            <p className="text-xs sm:text-sm text-zinc-400 leading-relaxed font-mono">
              Monitors market price distributions, exposes predatory BNPL rates via IRR/EAR, computes Indonesian customs landed cost, and executes purchases within signed Ed25519 bounds.
            </p>
          </div>

          {/* Quick Action Button Group */}
          <div className="flex flex-col sm:flex-row items-stretch lg:items-center gap-2.5">
            <button
              onClick={() => setIsMandateModalOpen(true)}
              className="px-4 py-2.5 rounded-lg bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-medium flex items-center justify-center gap-2 transition active:scale-[0.98] shadow-sm"
            >
              <KeyRound className="w-4 h-4 text-zinc-900" />
              {activeMandate ? 'Active Mandate (Signed)' : 'Sign Intent Mandate'}
            </button>
            <button
              onClick={handleTriggerScamSimulation}
              className="px-4 py-2.5 rounded-lg bg-zinc-900 hover:bg-zinc-850 border border-zinc-800 hover:border-zinc-700 text-zinc-300 text-xs font-mono flex items-center justify-center gap-2 transition"
            >
              <ShieldAlert className="w-4 h-4 text-zinc-400" />
              Simulate Outlier Scam
            </button>
          </div>
        </div>

        {/* Section 1: The One Number Reveal (Pre-Purchase Financial Comparison) */}
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-sm sm:text-base text-zinc-100">Live Product Evaluation</h3>
              <p className="text-[11px] font-mono text-zinc-500">Autonomous evaluation against signed Intent Mandate</p>
            </div>
          </div>

          <OneNumberCard
            itemTitle="Lenovo ThinkPad T14s Gen 4 (AMD Ryzen 7 PRO, 16GB RAM, 512GB SSD)"
            merchantName="Lenovo Official Store Australia (Cross-Border)"
            stickerPrice={1580}
            stickerCurrency="AUD"
            trueCost={17582248}
            targetCurrency="IDR"
            bnplBreakdown={{
              tenorMonths: 6,
              nominalApr: 0.18,
              effectiveAnnualRate: 0.195,
              totalFinanceCharge: 450000,
              isPredatory: false
            }}
            landedCostBreakdown={{
              spotFxRate: 10400,
              effectiveFxRate: 10660,
              fxMarkupCost: 410800,
              totalCustomsTaxes: 2423728,
              touristTaxRefund: 1684280
            }}
            optimalStopping={{
              decision: 'BUY',
              reservationPrice: 16600000,
              percentileRank: 16.7,
              daysLeft: 10,
              rationale: 'Optimal stopping indicates current pricing sits in the 16.7th percentile of historical quotes. Expected future variance yields lower probability of further drops before mandate deadline.'
            }}
            onExecutePurchase={handleExecuteCompliantPurchase}
            isExecuting={isExecuting}
            isSettled={isSettled}
          />
        </section>

        {/* Section 2: Time-Travel Replay Simulator & Benchmarking */}
        <section>
          <ReplaySimulator />
        </section>

        {/* Section 3: Immutable Audit & Banking Trail */}
        <section>
          <AuditTrailView
            transactions={transactions}
            executedOrders={executedOrders}
            disposableCards={disposableCards}
          />
        </section>

        {/* Minimalist Footer */}
        <footer className="pt-6 pb-8 border-t border-zinc-850 flex flex-col sm:flex-row items-center justify-between gap-3 text-[11px] font-mono text-zinc-500">
          <div>
            TrueCost Autopilot · FinTechathon 2026 International AI Track (Topic A)
          </div>
          <div>
            Deterministic Quant Math + Ed25519 Verifiable Mandates
          </div>
        </footer>
      </main>

      {/* Modals */}
      <MandateModal
        isOpen={isMandateModalOpen}
        onClose={() => setIsMandateModalOpen(false)}
        keyPair={keyPair!}
        onMandateCreated={handleMandateCreated}
      />

      <ScamInterventionModal
        isOpen={isScamModalOpen}
        onClose={() => setIsScamModalOpen(false)}
        onOverrideConfirm={() => {
          setIsScamModalOpen(false);
          alert('User override token issued. High-risk transaction logged in security audit ledger.');
        }}
        scamReasons={scamReasons}
        modifiedZScore={scamZScore}
        listingPrice={3990000}
      />
    </div>
  );
}

export default App;
