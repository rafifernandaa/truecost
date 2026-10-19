# TrueCost Autopilot — Presentation Deck & Demo Video Script

**FinTechathon 2026 (Shenzhen International FinTech Competition)**  
*International Track · Topic A: Personal Finance Assistant*  
**Theme:** "AI as a Financial Participant"  
**Duration Limits:** Presentation Deck $\le 10$ minutes | Demo Video $\le 5$ minutes

---

## Part 1: Presentation Slide Deck Outline (10-Minute Roadshow)

### Slide 1: Title & Team Introduction (0:00 - 0:45)
* **Title:** TrueCost Autopilot — AI as an Autonomous, Cryptographically Bounded Financial Participant
* **Subtitle:** Protecting Consumers from Deceptive BNPL, Cross-Border Friction, and E-Commerce Fraud
* **Team:** International Track Team (Overseas University Representation)
* **Key Visual:** System emblem showing user browser holding private key connecting to Core Banking via AP2 Mandates.

### Slide 2: The Core Problem: The Friction at the Point of Purchase (0:45 - 2:00)
* **Real Pain Points Lived by Consumers & Students:**
  1. *Deceptive "0% Installments":* Fine print hides admin fees; real effective APR exceeds 35%.
  2. *Cross-Border Landed Cost Shocks:* Foreign exchange (FX) card spread markups (+2.5%), destination customs import taxes (PPN/PPh), and missed tourist refunds (TRS).
  3. *APP Fraud & Scam Outliers:* Scammers exploit extreme price drops and high-pressure tactics.
* **The "Wrapper" Trap:** Current AI assistants are passive FAQ chat wrappers that hallucinate math and cannot safely touch bank rails.

### Slide 3: The Paradigm Shift: "AI as a Financial Participant" (2:00 - 3:15)
* **Not a Chatbot — An Agent with a Mandate:**
  * Borrowing from Google's Agent Payments Protocol (AP2) and Revolut's Execution Engine.
  * User signs an **Intent Mandate** with their private key in the browser.
  * The agent is delegated to monitor, calculate, and assemble a compliant **Cart Mandate**.
  * The Core Bank independently verifies signatures and hard budget caps before moving any funds.

### Slide 4: System Architecture (AIEP Model) (3:15 - 4:45)
* **Layer 1:** Client Interface & Web Crypto Ed25519 Signer (zero key transmission).
* **Layer 2:** Agentic Middle Workflow (Intake, Market Watcher, Decision, Audit, Execution).
* **Layer 3:** Deterministic Quant Engine (Pure NumPy/SciPy math; zero LLM arithmetic).
* **Layer 4:** Sandbox Core Bank (Double-entry ledger, Sinking Pot fund reservation, and Single-Use Disposable Virtual Cards).

### Slide 5: The Four Mathematical Pillars (Anti-Hallucination Core) (4:45 - 6:15)
1. **BNPL Lie Detector (IRR/EAR):** Solves exact root where $NPV(r) = 0$; exposes hidden APR.
2. **Landed Cost Engine:** Models Indonesian Bea Cukai ITA customs rules, card spreads, and Australian TRS refunds.
3. **Finite-Horizon Optimal Stopping ($R_t$):** Dynamic reservation price decay curve; mathematically dictates whether to buy immediately or hold.
4. **Boris Iglewicz & David Hoaglin Modified Z-Score ($M_i$):** Robust outlier detection using Median & MAD to isolate fraudulent pricing.

### Slide 6: Security, Compliance & Scam Defense (6:15 - 7:45)
* **4-Tier Permission Matrix:** Read-only (Tier 0) up to Anomaly Interventions (Tier 3).
* **Revolut-Style Scam Intervention Flow:** When $M_i < -3.5$, the transaction is paused by default, triggering diagnostic cognitive friction questions to break scammer urgency.
* **Disposable Virtual Cards:** Single-use tokens that self-destruct upon clearance, neutralizing post-purchase card theft.

### Slide 7: Live Execution Evidence & Benchmarks (7:45 - 8:45)
* **Physical Hardware Verification:** Live execution proof on Samsung Galaxy A55 5G (`SM-A556E`) showing all 4 Google Stitch screens operating natively with local cryptographic signing.
* **Machine-Readable Ledger:** Demonstration of `logs/sandbox_execution.jsonl`.
* **Adversarial Red-Team Results:** 100% of over-budget or tampered carts rejected by independent bank verification.
* **Performance:** Sub-50ms deterministic quant execution; 100% numeric groundedness with Audit Agent verification.

### Slide 8: Commercial Feasibility & WeBank Ecosystem Alignment (8:45 - 9:30)
* **Bank-Embeddable Solution:** Helps digital banks (like WeBank) promote responsible lending, curb consumer default on third-party BNPL traps, and eliminate APP fraud liability.
* **Future Extension:** FATE-based privacy-preserving collaborative risk modeling across cross-border banking partners.

### Slide 9: Conclusion & Q&A (9:30 - 10:00)
* **Summary:** TrueCost Autopilot bridges conversational AI with deterministic mathematical rigor and cryptographic security.
* **Open for Jury Questions.**

---

## Part 2: Demo Video Script ($\le$ 5 Minutes)

### [0:00 - 0:40] Scenario Introduction
* **Voiceover:** *"Meet Alex, an international student planning to buy a high-performance laptop. In front of him is an advertised sticker price of 1,580 AUD with an enticing '0% interest' installment plan. But is this really a good deal, and is it safe to buy? Today we demonstrate TrueCost Autopilot running natively on a physical Samsung Galaxy A55 5G smartphone connected to our sandbox banking backend."*
* **On-Screen:** Show the TrueCost Autopilot mobile application on the Samsung Galaxy A55 5G with live Sandbox Bank balances (Checking: 25,000,000 IDR) and the 4 Stitch-designed navigation tabs (Capture Canvas, Quant Verdict, Scam Shield, Audit Ledger).

### [0:40 - 1:40] Step 1: In-Browser Cryptographic Intent Mandate Signing
* **Action:** Alex clicks **"Sign Intent Mandate"**. Sets:
  - Max Budget: Rp 18,500,000
  - Purchase Horizon: 14 Days
  - Allowed Rails: Debit & Cash only (Max APR: 15%)
* **Voiceover:** *"Under the Google AP2 paradigm, Alex creates an Intent Mandate. Watch closely: Alex's browser generates an Ed25519 keypair and signs the mandate locally. Private keys never touch our server."*
* **On-Screen:** Click **"Sign Mandate"**. Highlight the Sinking Pot vault instantly locking 18,500,000 IDR from Checking, reserving funds.

### [1:40 - 2:40] Step 2: "The One Number" Reveal & Mathematical Evidence
* **Action:** The Market Watcher Agent evaluates the candidate listing.
* **Voiceover:** *"The One Number comparison reveals the truth: Advertised sticker is 1,580 AUD, but TrueCost is 17,582,248 IDR. Let's inspect the evidence drawer."*
* **On-Screen:**
  1. Open **BNPL Lie Detector**: Show nominal 0% vs true 19.5% EAR due to hidden charges.
  2. Open **Cross-Border Taxes & FX**: Show the Bea Cukai PPN/PPh import tax addition and the 10% Australian TRS tourist refund subtraction.
  3. Open **Optimal Stopping Curve**: Show that current price sits in the 16.7th percentile of historical prices—verifying an optimal **BUY** window.

### [2:40 - 3:40] Step 3: Revolut-Style Scam Intervention Flow
* **Action:** Alex tests a suspicious marketplace deal priced at Rp 3,990,000 (78% below median).
* **Voiceover:** *"What happens if Alex encounters an advance-fee scam listing? Our Modified Z-Score engine computes $M_i = -3.85$, instantly halting execution and launching the Scam Intervention Flow."*
* **On-Screen:** Show the modal pop-up with the 10-second reflection countdown and mandatory cognitive questions. Explain how this halts APP fraud.

### [3:40 - 4:30] Step 4: Autonomous Execution via Single-Use Disposable Token
* **Action:** Alex executes the verified ThinkPad purchase.
* **Voiceover:** *"The Execution Agent signs the Cart Mandate. The Core Bank independently verifies the signature chain and budget cap. Upon passing, the bank issues a single-use disposable card token that settles the payment and immediately self-destructs."*
* **On-Screen:** Sinking pot balance settles; disposable card transitions to `CONSUMED_DESTROYED`. Show the immutable event appending to the live audit log.

### [4:30 - 5:00] Step 5: Summary & Defense
* **Voiceover:** *"TrueCost Autopilot: 100% deterministic math, cryptographically verifiable mandates, and active scam protection. Transforming AI into a trustworthy financial participant."*
* **On-Screen:** End slide with GitHub repository link and FinTechathon 2026 track compliance summary.
