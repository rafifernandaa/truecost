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

---

## 3. Physical Android Device Verification (Hardware Execution Proof)

To validate production readiness beyond cloud and desktop environments, the complete TrueCost Autopilot client interface was deployed, installed, and evaluated on a physical target smartphone:
- **Device Model:** Samsung Galaxy A55 5G (`SM-A556E`)
- **Android OS:** Android 14 / One UI 6.1
- **Device Serial:** `RRCX305H0YE`
- **Application Package:** `com.truecost.autopilot` (`.MainActivity`)
- **APK Target:** `android_app/app/build/outputs/apk/debug/app-debug.apk`

### Verified Screen Flows on Hardware:
1. **Screen 1: Capture & Budget Canvas (`phone_screen_capture_real.png`)**  
   - Autonomous Intent Mandate creation with client-side Web Crypto Ed25519 key generation.  
   - Interactive camera / price-tag scan trigger and budget allocation sliders ($18.5M IDR cap).  
   - Live snapshot: [phone_screen_capture_real.png](file:///c:/Users/rafif/fintechathon26/phone_screen_capture_real.png)

2. **Screen 2: Deterministic Quant Verdict (`phone_screen_verdict.png`)**  
   - Effective APR calculation exposing hidden fees (43.8% EAR vs advertised 0%).  
   - Cross-border landed cost engine showing AUD to IDR conversion, TRS tax rebate (-10%), and Bea Cukai import tariff breakdown (+IDR 2.42M).  
   - Dynamic Optimal Stopping recommendation showing reservation threshold $R_4$.  
   - Live snapshot: [phone_screen_verdict.png](file:///c:/Users/rafif/fintechathon26/phone_screen_verdict.png)

3. **Screen 3: Scam Shield & HITL Execution Gate (`phone_screen_capture.png`)**  
   - Modified Z-Score outlier detection against historical price distributions.  
   - Revolut-style human-in-the-loop intervention flow for Tier 3 risk alerts with cognitive friction cooldown.  
   - Live snapshot: [phone_screen_capture.png](file:///c:/Users/rafif/fintechathon26/phone_screen_capture.png)

4. **Screen 4: Sandbox Bank & Trajectory Audit Ledger (`phone_screen.png`)**  
   - Cryptographic Ed25519 mandate verification chain (User Intent $\rightarrow$ Agent Cart $\rightarrow$ Core Bank).  
   - Virtual single-use card issuance (`VCARD_E8941AB9D721`) with atomic burn upon clearance.  
   - Double-entry ledger balance updates and sinking pot savings return.  
   - Live snapshot: [phone_screen.png](file:///c:/Users/rafif/fintechathon26/phone_screen.png)

### 3.1 Floating Dynamic Island Bottom Dock & Fluid Micro-Interactions (Physical Device Verification)
- **Floating Dynamic Island Dock Architecture:** Continuous floating capsule (358dp width, 68dp height, 24dp bottom offset, 36dp corner radius) rendered with frosted acrylic glass backdrop (`backdrop-filter: blur(24px)`, subtle 1dp border, ambient drop shadow).
- **Sliding Fluid Pill Indicator:** Navy pill (`#0B192C`, height 48dp, radius 24dp) with native spring physics (`cubic-bezier(0.34, 1.56, 0.64, 1)`). When switching tabs, active tab expands to show `[Icon + Bold White Micro-Label]` while inactive tabs compress into clean minimalist monochrome icons.
- **Interactive Upward Expansion Sheet (Micro-Context Switcher):** Tapping the live dual-currency status pill (`AUD/IDR` with pulsing emerald dot) or long-pressing dock tabs morphs the dock upward with spring physics into a floating rounded modal card (radius 32dp, elevation 20dp). Features active liquidity indicator (`$2,450.00 AUD · Safe Horizon +42d`) and 1-tap scenario presets (`01 BNPL Trap`, `02 AU Tax TRS`, `03 Scam Risk`).
- **Touch & Button Micro-Interactions:**
  - Deep cobalt blue Analyze button (`#0B2F9F`) with touch-down squeeze (`scale(0.92)`), circular spinner layout morph, and haptic green verified flash.
  - Center Viewfinder with corner breathing brackets animation (`2.4s ease-in-out` loop) and active pressed blue glow.
  - Benchmark cards with lift-on-tap elevation (`translateY(-4dp)`) and animated sliding top accent lines.
### 3.2 4-Screen Android Polished UI & Plain English UX (Samsung Galaxy A55 5G Verification)
- **Zero Developer Jargon & Placeholders:** Completely eliminated technical placeholders (`PART 01`, `SECTION 04.2`, `FOLIO SEC. 04`, `FIG. 4.1`, `AIEP Deterministic Pipeline Execution`) across all views in favor of plain English student-centric copy.
- **Resolved Layout Clipping & Cut-off Containers:**
  - Extended scroll container bottom inset to `pb-[110px]` so all bottom CTAs ("Export Transaction Log", "Keep Blocked", "Cross-Market Stores") scroll completely clear of the floating navigation bar.
  - Set top inset to `pt-[96px]` providing generous clearance below the fixed 56dp frosted header (`pt-safe`), eliminating any half-peeking or cut-off container bounds.
  - Standardized horizontal page margins to 20dp (`px-5`) and card gaps to uniform 14dp (`gap-3.5`).
- **Rebuilt Floating Dynamic Island Bottom Dock:**
  - Strict vertical stacking for all 4 navigation tabs (`[Capture]`, `[Verdict]`, `[Shield]`, `[Audit]`): 24dp Material Symbol icon placed directly on TOP with the 10sp bold label centered directly BELOW.
  - 1-Tap Instant Response (Fixed double-tap issue): Tab labels are visible continuously across active and inactive states. Buttons feature full quadrant tap targets (`flex-1 max-w-[76px]`), `touch-action: manipulation`, and active tap scale (`0.94`), switching tabs and states with zero horizontal layout shift on the first touch.
  - Active tab highlighted in deep cobalt blue (`#0B2F9F`) inside a soft rounded pill background (`rgba(11, 47, 159, 0.08)`, radius 20dp).
- **Physical Device Screen Snapshots:**
  - **Screen 1 — Capture Canvas:** [phone_screen1_capture_final.png](file:///c:/Users/rafif/fintechathon26/phone_screen1_capture_final.png) (Available balance `$2,450.00 AUD / ≈ Rp 25.400.000 IDR`, "42 Days Cash Buffer Safe", clean viewfinder, minimalist input, and 2-line demo benchmark cards).
### 3.3 Edge-to-Edge Luxury Aesthetic & Seamless Canvas Overhaul (Physical Hardware Proof)
- **Zero Dividers & Seamless Canvas Integration:**
  - Removed all rectangular top navbar boxes, enclosing header cards, and horizontal divider lines.
  - Seamless background canvas with subtle warm peach/radial light gradient (`#FFFDFB` into `#FAF8F5`).
  - Floating top controls in a single horizontal row (`px-[14px]`, `pt-safe`):
    * **Left:** Circular frosted glass 4-dot grid button (36x36dp, `rgba(255,255,255,0.75)`).
    * **Center:** Minimalist floating currency pill (height 32dp, `rgba(255,255,255,0.85)`, `AUD · IDR 10,360` with pulsing emerald dot).
    * **Right:** Notification bell with red alert dot (36x36dp) and circular student profile avatar (36x36dp).
  - Page Title Typography rendered directly on the seamless canvas below the controls (26sp semi-bold geometric sans `#141413`, 13sp muted graphite subtitle `#64748B`, zero clipping).
- **Tightened Modern Card Geometry:**
  - Tightened outer horizontal page margins from 20dp to 14dp (`px-[14px]`) for an expansive edge-to-edge flagship feel.
  - Pure milk white (`#FFFFFF`) card surfaces with 0.5dp specular border (`rgba(0,0,0,0.04)`) and soft ambient diffusion shadow (`shadow-[0_8px_24px_rgba(15,23,42,0.04)]`).
  - Standardized 24dp corner radii for primary cards and 18dp for internal metric tiles; 10dp inter-card spacing (`gap-2.5`).
- **Detached Floating Navigation Dock (Reference Video Mechanics):**
  - Detached floating capsule anchored at bottom (360dp width, 68dp height, 16dp bottom offset, 34dp corner radius, `rgba(255,255,255,0.95)`, `backdrop-filter: blur(24px)`).
  - 3 Primary Tabs (`[Capture]`, `[Verdict]`, `[Shield]`) with 22dp line icon centered on top and 10sp micro-label directly below.
  - Active tab wrapped inside dedicated soft-blue capsule background (width 68dp, height 50dp, radius 22dp, `#EBF2FA`) with liquid spring physics.
  - Right edge session avatar capsule (48x48dp, 24dp radius) with `TC` avatar and `"Demo"` micro-badge.
- **Interactive Upward Spring Expansion Sheet (Micro-Context Switcher):**
  - Tapping right session capsule or top currency pill morphs the dock upward into a floating rounded modal card (radius 28dp, height ~260dp, shadow `0 20px 60px rgba(15,23,42,0.22)`).
  - 3 selectable scenario rows with radio pills and status dots:
    * `01 BNPL Trap (MacBook Air)` · `18.4% APR`
    * `02 AU Tax TRS (ThinkPad)` · `+10% Back`
    * `03 Scam Risk (ROG 4080)` · `Blocked`
  - Tapping a row triggers an elastic radio bounce, activates the scenario, and smoothly collapses back into the floating dock.
- **Hardware Screen Snapshots (Samsung Galaxy A55 5G):**
  - **Screen 1 — Luxury Capture Canvas:** [phone_screen1_luxury.png](file:///c:/Users/rafif/fintechathon26/docs/screenshots/phone_screen1_luxury.png)
  - **Screen 2 — Luxury Deal Analysis (Verdict):** [phone_screen2_luxury.png](file:///c:/Users/rafif/fintechathon26/docs/screenshots/phone_screen2_luxury.png)
  - **Screen 3 — Luxury Scam Shield:** [phone_screen3_luxury.png](file:///c:/Users/rafif/fintechathon26/docs/screenshots/phone_screen3_luxury.png)
  - **Screen 4 — Student Safety Log & Ledger:** [phone_screen4_luxury.png](file:///c:/Users/rafif/fintechathon26/docs/screenshots/phone_screen4_luxury.png)
  - **Micro-Context Upward Expansion Sheet:** [phone_sheet_luxury.png](file:///c:/Users/rafif/fintechathon26/docs/screenshots/phone_sheet_luxury.png)


