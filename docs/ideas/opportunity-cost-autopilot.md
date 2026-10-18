# TrueCost Autopilot: Opportunity Cost & Human Capital Engine

## Problem Statement
How might we transform TrueCost from a reactive scam/price-check barrier into an active financial catalyst that reframes impulsive spending as tangible human and financial capital growth tailored to who the user is?

## Recommended Direction
An **Active Opportunity Cost Decision Gate** seamlessly embedded into the Verdict Screen and Onboarding Flow:
1. **15-Second Onboarding Profiler:**
   - **Age Bracket:** Student (18–22), Early Career (23–28), Mid Career (29–38), Senior (39+)
   - **Professional Role:** Tech & Software, Creative & Design, Business & Finance, Student / Academic
   - **Monthly Discretionary Budget & Growth Target:** High-Yield Wealth, Career Skill Mastery, Financial Independence
2. **Dual-Lens Opportunity Visualizer on the Verdict Screen:**
   - **Lens 1: Compound Financial Growth** — Interactive horizon selector (1y, 3y, 5y, 10y) showing future compounded value at 2% (conservative cash) up to 7% (index growth).
   - **Lens 2: Human Capital Alternative** — Tailored to the user's role (e.g., for Tech: AWS Certification + AI Academy subscription + Ergonomic gear).
3. **1-Tap Actionable Interventions:**
   - ⚡ **"Divert to Growth Pot"**: Instantly locks the sticker price into the user's high-yield savings pot via an Ed25519-signed mandate.
   - ⏳ **"24h Opportunity Freeze"**: Enforces an intentional impulse cool-down timer.

## Key Assumptions to Validate
- [ ] Users engage more with concrete career items than abstract percentage gains.
- [ ] The 3-card onboarding flow takes under 15 seconds with zero abandonment.
- [ ] Diverting to the growth pot increases perceived financial empowerment.

## MVP Scope
- `backend/app/engine/opportunity_cost.py`: Pure NumPy deterministic compounding pricer + role growth matrix.
- `backend/tests/test_opportunity_cost.py`: Complete unit test suite verifying zero floating-point drift and correct compounding math.
- `backend/app/api/routes.py`: Endpoint `POST /api/v1/quant/opportunity-cost` returning dynamic compound trajectory and role-tailored human capital alternatives.
- `android_app/app/src/main/assets/www/index.html`:
  - 3-card glassmorphic onboarding profiler with persistence.
  - Interactive Opportunity Cost card with Compounding / Human Capital tabs and "Divert to Growth Pot" action button.
- Synced across `frontend/public/android/`, `frontend/dist/android/`, and `android_assets/`.

## Not Doing (and Why)
- **External Brokerage API (Interactive Brokers / Plaid)**: Keeps setup sandbox-native, zero-credential-leak compliant, and avoids third-party rate limits.
- **LMS Course Scrapers**: We use a curated high-impact catalog rather than live scrapers to prevent broken links and maintain deterministic math.
- **Complex Multi-Year Tax Bracket Modeling**: Unnecessary complexity for the FinTechathon MVP; simple pre-tax/post-tax compounding suffices.

## Open Questions & Decisions
- **Growth Pot Accounting:** Diverting to the growth pot debits the Safe-to-Spend balance and credits the `growth_sinking_pot` in `SandboxBank`, immediately updating the Hero card balance.
