# TrueCost Autopilot — Execution Evidence & Audit Log

**FinTechathon 2026 (Shenzhen International FinTech Competition)**  
*International Track · Topic A: Personal Finance Assistant*  
**Submission Requirement:** Item 6 (Simulated-Account / Sandbox Operation Logs & Execution Trail)

---

## 1. Overview of Execution Evidence

Per Section 5 of the Competition Rules (`international-topics-rules-en.docx`), teams submitting under non-on-chain topics must provide **simulated-account / sandbox operation logs** demonstrating that the AI operates as an autonomous financial participant rather than a static chat interface.

The complete machine-readable audit trail is stored in:
- `logs/sandbox_execution.jsonl`

---

## 2. End-to-End Execution Flow (Chronological Trajectory)

### Event 1: User Cryptographic Intent Mandate Registration
- **Mandate ID:** `MANDATE-2026-FINTECH-001`
- **Target Item:** Lenovo ThinkPad T14s Gen 4 (16GB RAM, 512GB SSD)
- **Authorized Maximum Budget:** IDR 18,500,000.00
- **Allowed Payment Rail:** `["DEBIT", "CASH"]` (Zero unverified debt permitted)
- **Max Acceptable APR:** 15.0%
- **Cryptographic Signature:** Valid Ed25519 signature generated in user's browser.
- **Banking Action:** Core Bank automatically creates a **Dedicated Sinking Fund Pot** (`ACC_USER_SINKING_POT`) and reserves IDR 18,500,000 from Checking (`ACC_USER_CHECKING`), guaranteeing funds availability.

```json
{
  "event": "INTENT_MANDATE_REGISTERED",
  "mandate_id": "MANDATE-2026-FINTECH-001",
  "reserved_funds": 18500000.0,
  "status": "REGISTERED"
}
```

---

### Event 2: Autonomous Market Watching & Optimal Timing
- **Day 4 of 14 Horizon:**
- **Observed Price:** IDR 16,400,000.00 (Percentile rank: 16.7% lowest in historical distribution).
- **Dynamic Reservation Price Threshold ($R_4$):** IDR 16,600,000.00.
- **Decision Engine Output:** **`BUY`**
- **Econometric Rationale:** Current price is strictly below the optimal stopping reservation threshold; expected incremental utility of waiting remaining 10 days is mathematically lower than securing this verified deal.

---

### Event 3: Cross-Border Landed Cost Calculation
- **Source Market:** Lenovo Official Store Australia (AUD 1,580.00).
- **Effective FX Conversion:** 1 AUD = 10,660.00 IDR (including 2.5% card FX spread).
- **Australian Tourist Refund Scheme (TRS):** 10% GST refund deducted (-IDR 1,684,280.00).
- **Indonesian Customs (Bea Cukai) Import Taxes:** IDR 2,423,728.80 (0% duty under WTO ITA, 11% PPN, 7.5% PPh with NPWP).
- **Net Final Landed Cost:** **IDR 17,582,248.80** (Strictly within the IDR 18,500,000 budget cap).

---

### Event 4: Anti-Fraud & Scam Risk Audit
- **Price Anomaly Metric:** Modified Z-Score = -0.85 (Conforms to authentic retail distribution).
- **Seller Reputation:** 98.5% positive rating, 340 completed transactions, 520 days account age.
- **Domain Verification:** Verified eBay Australia merchant (`ebay.com.au`), zero typosquatting detected.
- **Scam Score:** **0.00** -> **`PROCEED_SAFE`**.

---

### Event 5: Cryptographic Settlement & Single-Use Disposable Card
1. The **Execution Agent** issues and cryptographically signs `CART-2026-EXEC-099`.
2. The **Core Bank** independently re-validates:
   - User Intent Mandate signature: **VALID**
   - Agent Cart Mandate signature: **VALID**
   - Budget boundary (IDR 17,582,248.80 $\le$ IDR 18,500,000.00): **PASSED**
   - Method permitted (`DEBIT`): **PASSED**
   - Scam threshold ($0.00 < 0.50$): **PASSED**
3. Bank generates single-use virtual card `VCARD_E8941AB9D721` with exact spending limit.
4. Settlement completes atomically; disposable card transitions immediately to **`CONSUMED_DESTROYED`** to eliminate card theft risks.
5. Sinking pot balance reflects remaining savings of **IDR 917,751.20** returned to the user's primary checking account.

---

### Event 6: Adversarial / Rogue Agent Attack Rejection Test
- **Attacker Action:** Compromised agent attempts to dispatch `CART-ROGUE-ATTACK` for IDR 25,000,000.00.
- **Bank Defense:** Independent Bank Policy Verifier immediately catches the breach:
  `[BUDGET_EXCEEDED] Cart landed cost (25,000,000 IDR) exceeds user authorized cap (18,500,000 IDR).`
- **Result:** Transaction terminated and rejected; zero funds moved. Audit incident logged in security ledger.
