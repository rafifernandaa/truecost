# The Living Financial Core (Topic A Linear Onboarding)

## Problem Statement
How might we transform TrueCost Autopilot's 4-page onboarding from four disconnected visual templates into a single, linear, interactive **Topic A (Personal Finance Assistant)** journey where one morphing centerpiece and one correlated personal finance scenario (`$2,450` monthly budget vs. a `$1,200` bill) evolve continuously from intake to autonomous execution?

## Recommended Direction
We unify all four pages into a single **4-Act Personal Finance Autopilot Story** aligned with the FinTechathon 2026 International Track rules (**Topic A: Personal Finance Assistant** — *smart budgeting, bill analysis, and spending insights, delivering actionable recommendations based on the user's income and expenses* under the theme *"AI as a Financial Participant"*).

### Three Continuity Threads Across All 4 Pages:
1. **Thread 1 — Atmospheric Dawn-to-Daylight Horizon:**
   - **Act 01 (Smart Budgeting Intake):** Deep Obsidian (`#131522`) with a rising Cobalt/Coral horizon glow (`25%`).
   - **Act 02 (Bill & BNPL X-Ray):** Twilight Obsidian-to-Alabaster transition (`55%` risen horizon) framing the Squircle Mesh Lens and sculpted frosted arch.
   - **Act 03 (Spending Insights & Timing):** Warm Morning Cream (`#FDF6E4` + Cobalt/Coral radial contour, `85%` risen).
   - **Act 04 (Autonomous Guardrails & Vault):** Full Muestra-64 Alabaster (`#F4F0EA`, `100%` daylight), matching the main app dashboard with zero visual seam.

2. **Thread 2 — Persistent "Live Budget Ledger" Header Strip:**
   Directly below the connected `01 ── 02 ── 03 ── 04` progress track sits a persistent **Live Case Pill** anchored in the exact same coordinates across all 4 pages, updating dynamically as the AI works:
   - **Act 01:** `Budget $2,450 · Target Bill $1,200 (49% Buffer)`
   - **Act 02:** `Bill X-Ray: 17.9% True EAR (+$120 Hidden Drain)`
   - **Act 03:** `Spending Insight: Wait 4d → $1,055 (-$145 Saved)`
   - **Act 04:** `AP2 Mandate Ready: $1,055 Cap (+$265 Protected)`

3. **Thread 3 — One Morphing Centerpiece ("The Living Core") + Live State Handoff:**
   - **Act 01 · The Intake Sphere (Smart Budgeting):** 3D Liquid Plasma Orb. User selects from 3 correlated Topic A Personal Finance scenarios (*"$1,200 Work Laptop Bill"*, *"$850 Home Appliance Upgrade"*, or *"$640 Monthly Subscriptions & BNPL Audit"*). All subsequent pages (`02`, `03`, `04`) dynamically recalculate their exact numbers based on this choice.
   - **Act 02 · The X-Ray Squircle Lens (Bill & Fee Analysis):** The Orb morphs into a faceted Squircle Mesh Jewel above a recessed frosted arch. Tapping each bill line item exposes hidden BNPL/installment fees using deterministic SciPy IRR math (`0% Hallucination`).
   - **Act 03 · The Chrono-Valley Dial (Spending Insights & Cashflow Timing):** The Squircle opens into a circular Topographic Price-Valley Dial with an overlapping floating status bubble (`Day 04 / 14 · Buy Window ★ · 16.7% pctl`). Tapping Day 1 / Day 4 / Day 9 demonstrates optimal stopping that preserves the user's 60-day emergency cashflow buffer.
   - **Act 04 · The Guardian Vault Trio (AI as a Financial Participant):** Three tactile eye-tracking Guardians (`BNPL Guard`, `0-PII Scrubber`, `MAD Z-Score Shield`) watch over the pre-signed Ed25519 Intent Mandate card. Tapping **"Enter Autopilot →"** hands the active scenario and budget state directly into the main dashboard and DeepSeek V3 co-pilot.

## Key Assumptions to Validate
- [x] **Strict Topic A Focus:** Every headline, badge, and calculation highlights personal budgeting, bill analysis, income-vs-expense buffer protection, and actionable spending insights.
- [x] **Linear Visual & Data Correlation:** Selecting any scenario on Page 1 updates the exact dollar amounts on Pages 2, 3, and 4, and carries into the main app on completion.
- [x] **Zero OS Status Bar Duplication:** Native Android status bar clearance without any fake clock or battery icons.

## MVP Scope
- Connected 4-step progress bar (`01 ── 02 ── 03 ── 04`) + persistent **Live Budget Ledger Strip** across all 4 pages.
- 3 selectable Topic A Personal Finance scenarios on Page 1 that dynamically drive the math on Pages 2, 3, and 4.
- Dawn-to-Daylight background progression (`#131522` → Twilight Blend → `#FDF6E4` → `#F4F0EA`).
- Live state handoff from Page 4 into the main dashboard and DeepSeek V3 prompt input.
- Full implementation in both `android_app/app/src/main/assets/www/index.html` and `frontend/src/components/OnboardingFlow.tsx`.

## Not Doing (and Why)
- **No disconnected visual templates:** Every screen shares the unified Muestra-64 palette, connected progress track, persistent Live Ledger strip, and morphing geometric core.
- **No Topic C cross-border/remittance focus in onboarding:** Keeps 100% alignment with Topic A (Personal Finance Assistant).
- **No fake status bar clock/wifi/battery icons:** Uses clean native inset spacing.
