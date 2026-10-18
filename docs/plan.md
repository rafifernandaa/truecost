# Implementation Plan: TrueCost — Pre-Purchase & Cross-Border Financial Agent

## Overview
Build a containerized, end-to-end Multi-Agent financial system for the FinTechathon 2026 International Track[cite: 1, 2, 3]. The system captures offline price tags/barcodes, online product URLs, or cross-border invoices, redacts PII prior to LLM invocation, fetches comparable international listings and FX/customs rules, computes all financial and statistical metrics inside a deterministic Python `QuantEngine`[cite: 3], enforces 0% numeric hallucination via an `AuditAgent`, and executes permission-tiered banking actions inside a SQLite Sandbox Bank with full trajectory logging[cite: 1, 2, 3].

## Dependency Graph

```text
src/config.py + src/agents/schemas.py (Pydantic v2 Contracts)
    │
    ├──► data/* + src/quant/loader.py
    │       └──► src/quant/pricing.py + src/quant/finance.py + src/quant/fraud.py
    │               └──► src/quant/engine.py (QuantEngine Facade)
    │
    ├──► src/sandbox_bank/models.py
    │       └──► src/sandbox_bank/service.py + src/sandbox_bank/seed.py
    │
    └──► src/telemetry/trajectory.py + src/agents/router.py (AIEP Model Matrix)
            ├──► src/agents/capture.py (Barcode + PII Redaction + Vision OCR)
            ├──► src/agents/market.py (eBay Browse API + Frankfurter FX + Customs)
            └──► src/agents/planner.py ──► src/agents/audit.py ──► src/agents/execution.py
                                                                        │
                                                                        ▼
                                                                 src/main.py (FastAPI)
                                                                   ├──► web/* (React UI)
                                                                   └──► scripts/run_benchmarks.py + docs/*
                                                                   

Architecture DecisionsZero LLM Arithmetic: All pricing, econometric regression, discounted cash flow, FX conversion, and tax calculations execute in src/quant/ using numpy and scipy; AuditAgent rejects any number in PlannerAgent output not traceable to QuantVerdict.   Mainland China Reachability (AIEP Model Matrix): src/agents/router.py abstracts model calls across Alibaba Cloud DashScope (qwen-vl-max, qwen2.5-14b-instruct), DeepSeek (deepseek-chat), and Google Gemini (gemini-2.5-flash) with deterministic local JSON caching so on-site demos in Shenzhen never fail on external network blocks.   Offline-Resilient External Tools: MarketAgent wraps live eBay Browse API and Frankfurter FX calls with an automatic fallback to data/market_fallback_cache.json to guarantee 100% uptime during judge evaluation.   ACID Sandbox Ledger with Idempotency: All Tier 2 and Tier 3 mutations require a unique idempotency_key and a cryptographic hitl_confirmation_token before committing state changes in SQLite.   Parallelization MatrixParallel Track A (Quant & Data): Tasks 2, 3, 4, 5 (src/quant/*, data/*)Parallel Track B (Sandbox Bank): Task 6 (src/sandbox_bank/*)Parallel Track C (Telemetry & Ingestion): Tasks 7, 8, 9 (src/telemetry/*, src/agents/router.py, capture.py, market.py)Sequential Integration: Task 1 must complete first; Tasks 10–14 depend on Tracks A, B, and C converging.Task List IndexPhase 1: Foundation & Pricing Core[ ] Task 1: Initialize Project Skeleton, Config, and Shared Pydantic Contracts[ ] Task 2: Seed Reference Laptop Dataset, Customs Rules, and Fallback Market Cache[ ] Task 3: Implement Pricing Quant Module (pricing.py)[ ] Checkpoint 1: Foundation & Pricing MathPhase 2: Financial Math, Fraud Engine & Sandbox Bank[ ] Task 4: Implement Finance Quant Module (finance.py)[ ] Task 5: Implement Fraud Scorer and Unified QuantEngine Facade (fraud.py, engine.py)[ ] Task 6: Build Sandbox Bank SQLite Ledger and Persona Seed (sandbox_bank/*)[ ] Checkpoint 2: Complete Deterministic Core & Sandbox BankPhase 3: Model Matrix, Telemetry & Ingestion Agents[ ] Task 7: Implement Trajectory Logger and Provider-Agnostic Model Matrix Router[ ] Task 8: Implement CaptureAgent with Barcode Decode, PII Redaction, and Vision OCR[ ] Task 9: Implement MarketAgent for eBay Browse API, Frankfurter FX, and Customs Lookup[ ] Checkpoint 3: Ingestion, Telemetry & External Data ToolsPhase 4: Decision Pipeline, Guardrails & FastAPI Backend[ ] Task 10: Implement PlannerAgent and Deterministic AuditAgent Guardrail[ ] Task 11: Implement Tiered ExecutionAgent and FastAPI Endpoints[ ] Checkpoint 4: End-to-End Multi-Agent API & Security GatePhase 5: Web UI, Benchmarks & Submission Bundle[ ] Task 12: Build Responsive Web Client Capture and TrueCost Breakdown Views[ ] Task 13: Build Web Client Scam Alert, HITL Confirmation Modal, and Trajectory Drawer[ ] Task 14: Implement 30-Case Benchmark Runner and Generate Compliance Artifacts[ ] Checkpoint 5: Full Stack MVP, Benchmarks & Submission BundleRisks and MitigationsRiskImpactMitigationeBay API rate-limit or credential approval delayHighPre-populate data/market_fallback_cache.json with 30 real captured laptop listing payloads in Task 2[cite: 3].Mainland China firewall blocks US LLM APIs during Shenzhen finalsHighDefault production profile in router.py uses DashScope Qwen + DeepSeek with local response caching[cite: 2, 3].LLM invents ungrounded numbers in advisory summaryHighAuditAgent regex-extracts all numbers and substitutes a deterministic template if any float deviates $> 10^{-2}$ from QuantVerdict[cite: 2, 3].pyzbar shared library (libzbar0) missing in containerMedExplicitly install libzbar0 in Dockerfile during Task 1[cite: 3].
---

### File 2: `tasks/todo.md`

```markdown
# Incremental Task Breakdown: TrueCost MVP

## Task 1: Initialize Project Skeleton, Config, and Shared Pydantic Contracts

**Description:** Set up the Python project configuration, Docker environment (including `libzbar0` system dependency), environment variable loader, and all cross-module Pydantic v2 data contracts (`ExtractedItem`, `MarketOffer`, `QuantVerdict`, `AuditReport`, `BankActionRequest`, `TrajectoryRecord`)[cite: 2, 3].

**Acceptance criteria:**
- [ ] `src/agents/schemas.py` defines strict Pydantic v2 models with field bounds for all inter-agent payloads and `QuantVerdict`[cite: 3].
- [ ] `src/config.py` loads LLM provider settings (`gemini`, `dashscope`, `deepseek`), API keys, and SQLite URI with safe defaults[cite: 3].
- [ ] `docker-compose.yml` builds the Python 3.11 backend image cleanly with `libzbar0` installed[cite: 2, 3].

**Verification:**
- [ ] Tests pass: `pytest tests/test_schemas.py -v`
- [ ] Build succeeds: `docker compose config -q && python -c "import src.config, src.agents.schemas"`
- [ ] Manual check: Verify `QuantVerdict` raises `ValidationError` when `permission_tier` is outside `0..3` or `scam_probability` is outside `0.0..1.0`[cite: 3].

**Dependencies:** None

**Files likely touched:**
- `pyproject.toml`
- `docker-compose.yml`
- `src/config.py`
- `src/agents/schemas.py`
- `tests/test_schemas.py`

**Estimated scope:** Medium (5 files)

---

## Task 2: Seed Reference Laptop Dataset, Customs Rules, and Fallback Market Cache

**Description:** Create the static 500-row standardized laptop dataset (`laptop_reference_500.csv`) for pre-fitting the Hedonic Ridge regression model, encode official Australian TRS and Indonesian import duty/PPN thresholds in `customs_rules.json`, and populate `market_fallback_cache.json` for offline demo reliability[cite: 3].

**Acceptance criteria:**
- [ ] `data/laptop_reference_500.csv` contains 500 valid rows with columns `cpu_mark,gpu_mark,ram_gb,ssd_gb,weight_kg,is_oled,price_aud`[cite: 3].
- [ ] `data/customs_rules.json` encodes AU TRS (`min_spend_aud: 300.0`, `gst_divisor: 11.0`) and ID customs personal baggage/import tax rules[cite: 3].
- [ ] `src/quant/loader.py` loads and validates all three data files into memory in `< 100ms`.

**Verification:**
- [ ] Tests pass: `pytest tests/test_loader.py -v`
- [ ] Build succeeds: `python -c "from src.quant.loader import load_reference_laptops, load_customs_rules; assert len(load_reference_laptops()) == 500"`
- [ ] Manual check: Inspect `data/customs_rules.json` to confirm official citations are included in metadata fields[cite: 3].

**Dependencies:** Task 1

**Files likely touched:**
- `data/laptop_reference_500.csv`
- `data/customs_rules.json`
- `data/market_fallback_cache.json`
- `src/quant/loader.py`
- `tests/test_loader.py`

**Estimated scope:** Medium (5 files)

---

## Task 3: Implement Pricing Quant Module (`pricing.py`)

**Description:** Implement the deterministic statistical pricing methods in `src/quant/pricing.py`: Median/MAD Robust Z-score, empirical historical price-drop probability, fake-discount comparison, Hedonic Ridge regression ($\lambda = 1.0$), and Entropy/User-Weighted TOPSIS ranking[cite: 3].

**Acceptance criteria:**
- [ ] `compute_robust_z(target_price, market_prices)` and `compute_drop_probability(history, k_pct, horizon_days)` match analytical hand-calculated test fixtures[cite: 3].
- [ ] `HedonicPricer` fits Ridge regression on `laptop_reference_500.csv` and predicts spec-adjusted fair price $\hat{p}_{\text{hedonic}}$ and residual percentage[cite: 3].
- [ ] `rank_offers_topsis(offers, weights)` returns bounded closeness scores $C_i^* \in [0.0, 1.0]$ and ranks dominant offers first[cite: 3].

**Verification:**
- [ ] Tests pass: `pytest tests/test_quant_pricing.py -v --cov=src.quant.pricing`
- [ ] Build succeeds: `ruff check src/quant/pricing.py tests/test_quant_pricing.py`
- [ ] Manual check: Run a one-liner printing the Hedonic fair value of a 16GB/512GB laptop vs. a 32GB/1TB laptop and confirm monotonic price scaling[cite: 3].

**Dependencies:** Task 1, Task 2

**Files likely touched:**
- `src/quant/pricing.py`
- `tests/test_quant_pricing.py`

**Estimated scope:** Small (2 files)

---

## Checkpoint 1: After Tasks 1–3 (Foundation & Pricing Math)
- [ ] All tests pass: `pytest tests/test_schemas.py tests/test_loader.py tests/test_quant_pricing.py -v`
- [ ] Reference datasets load without error and Hedonic/TOPSIS math is 100% deterministic[cite: 3].
- [ ] Review with human before proceeding to Phase 2.

---

## Task 4: Implement Finance Quant Module (`finance.py`)

**Description:** Implement deterministic financial discounting and cross-border cost methods in `src/quant/finance.py`: `brentq` IRR solver for annualized Effective APR of BNPL/installments versus cashback card, 36-month NPV Total Cost of Ownership, cross-border landed cost (incorporating FX spread, AU TRS refund, and ID duties), and 60-day cash-flow liquidity projection[cite: 3].

**Acceptance criteria:**
- [ ] `compute_effective_apr()` solves monthly IRR via `scipy.optimize.brentq` and outputs accurate annualized APR for deceptive "0% interest + monthly fee" BNPL schedules[cite: 3].
- [ ] `compute_tco_npv()` and `compute_landed_cost()` accurately apply AU TRS ($\frac{P}{11}$ if $\ge 300\text{ AUD}$), bank FX spread, shipping, and ID import taxes[cite: 3].
- [ ] `project_cashflow_60d()` simulates daily balances and sets `liquidity_breach = True` whenever projected minimum balance drops below `safety_buffer_aud`[cite: 3].

**Verification:**
- [ ] Tests pass: `pytest tests/test_quant_finance.py -v --cov=src.quant.finance`
- [ ] Build succeeds: `ruff check src/quant/finance.py tests/test_quant_finance.py`
- [ ] Manual check: Verify a $1,500 AUD laptop with a $10/month BNPL account fee over 12 months yields a positive double-digit Effective APR when accounting for foregone 1.5% card cashback[cite: 3].

**Dependencies:** Task 1, Task 2

**Files likely touched:**
- `src/quant/finance.py`
- `tests/test_quant_finance.py`

**Estimated scope:** Small (2 files)

---

## Task 5: Implement Fraud Scorer and Unified QuantEngine Facade (`fraud.py`, `engine.py`)

**Description:** Implement Empirical Bayes seller trust shrinkage and composite logistic scam/invoice-fraud probability scoring in `src/quant/fraud.py`, and wire all pricing, finance, and fraud functions into a single `QuantEngine.evaluate()` facade in `src/quant/engine.py` returning a validated `QuantVerdict`[cite: 3].

**Acceptance criteria:**
- [ ] `compute_scam_score()` outputs $S_{\text{scam}} \ge 0.85$ with explicit reason codes when given an extreme low-side price outlier ($Z_{\text{robust}} < -2.5$) combined with low seller feedback or an invoice IBAN/domain mismatch[cite: 3].
- [ ] `QuantEngine.evaluate()` executes all 7 quantitative methods deterministically in `< 50ms` and populates `recommended_action` and `permission_tier` (`0..3`)[cite: 3].
- [ ] Zero LLM calls or external network dependencies exist anywhere inside `src/quant/`[cite: 3].

**Verification:**
- [ ] Tests pass: `pytest tests/test_quant_fraud.py -v --cov=src.quant`
- [ ] Build succeeds: `ruff check src/quant/ tests/test_quant_fraud.py`
- [ ] Manual check: Inspect the JSON output of `QuantEngine.evaluate()` on a mock scam invoice and verify `recommended_action == "BLOCK_SCAM"` and `permission_tier == 3`[cite: 3].

**Dependencies:** Task 3, Task 4

**Files likely touched:**
- `src/quant/fraud.py`
- `src/quant/engine.py`
- `tests/test_quant_fraud.py`

**Estimated scope:** Medium (3 files)

---

## Task 6: Build Sandbox Bank SQLite Ledger and Persona Seed (`sandbox_bank/*`)

**Description:** Build the SQLAlchemy 2.0 SQLite models and transactional ledger service for the student persona (multi-currency AUD/IDR accounts, debit/credit cards, BNPL offers, sinking-fund savings pots, conditional `buy-if-price-below-X` escrow orders, and idempotency keys)[cite: 3].

**Acceptance criteria:**
- [ ] `src/sandbox_bank/seed.py` initializes a student profile with AUD and IDR balances, a 1.5% cashback card, and 2 BNPL plans[cite: 3].
- [ ] `SandboxBankService` supports `pay_with_card()`, `decline_bnpl_and_open_pot()`, and `place_price_trigger_order()` with ACID balance/escrow deductions[cite: 3].
- [ ] Duplicate requests with the same `idempotency_key` return the original transaction receipt without double-charging the account[cite: 3].

**Verification:**
- [ ] Tests pass: `pytest tests/test_sandbox_bank.py -v --cov=src.sandbox_bank`
- [ ] Build succeeds: `python -m src.sandbox_bank.seed`
- [ ] Manual check: Run `python -m src.sandbox_bank.seed` and verify SQLite database tables are populated cleanly[cite: 3].

**Dependencies:** Task 1

**Files likely touched:**
- `src/sandbox_bank/models.py`
- `src/sandbox_bank/service.py`
- `src/sandbox_bank/seed.py`
- `tests/test_sandbox_bank.py`

**Estimated scope:** Medium (4 files)

---

## Checkpoint 2: After Tasks 4–6 (Complete Deterministic Core & Sandbox Bank)
- [ ] All tests pass: `pytest tests/ -v --cov=src/quant --cov=src/sandbox_bank --cov-fail-under=95`
- [ ] `QuantEngine` and `SandboxBankService` operate end-to-end with 100% deterministic unit test coverage[cite: 3].
- [ ] Review with human before proceeding to Phase 3.

---

## Task 7: Implement Trajectory Logger and Provider-Agnostic Model Matrix Router

**Description:** Build the append-only JSONL trajectory logger (`src/telemetry/trajectory.py`) and the AIEP Model Matrix router (`src/agents/router.py`) supporting Alibaba DashScope (Qwen), DeepSeek, and Google Gemini with latency/token telemetry and deterministic file caching[cite: 2, 3].

**Acceptance criteria:**
- [ ] `TrajectoryLogger.log_step()` appends structured JSONL entries containing `trace_id`, `agent_name`, `model_id`, `input_hash`, `quant_outputs`, `audit_verdict`, `permission_tier`, `latency_ms`, and `tokens_used`[cite: 1, 2, 3].
- [ ] `LLMRouter` switches seamlessly between `dashscope`, `deepseek`, and `gemini` via `LLM_PROVIDER` env var and falls back to cached deterministic responses when `OFFLINE_DEMO_MODE=true`[cite: 3].
- [ ] Every router call automatically records latency and token metrics into the active trace[cite: 2, 3].

**Verification:**
- [ ] Tests pass: `pytest tests/test_router_telemetry.py -v`
- [ ] Build succeeds: `ruff check src/telemetry/ src/agents/router.py`
- [ ] Manual check: Trigger a mock router call in offline mode and verify a valid JSONL line is written to `docs/execution_evidence/trajectory.jsonl`[cite: 1, 3].

**Dependencies:** Task 1

**Files likely touched:**
- `src/telemetry/trajectory.py`
- `src/agents/router.py`
- `tests/test_router_telemetry.py`

**Estimated scope:** Medium (3 files)

---

## Task 8: Implement CaptureAgent with Barcode Decode, PII Redaction, and Vision OCR

**Description:** Implement `CaptureAgent` (`src/agents/capture.py`) to decode EAN/UPC barcodes via `pyzbar` first, scrub PII (Luhn PANs, 16-digit NIKs, passports, emails, phone numbers) from raw text and images, and extract structured laptop specs or cross-border invoice fields via Vision LLM fallback[cite: 2, 3].

**Acceptance criteria:**
- [ ] `redact_pii_text()` and image bounding-box scrubber mask 100% of Luhn-valid card numbers, NIKs, passport numbers, emails, and phone numbers before any LLM call[cite: 2, 3].
- [ ] Barcode images resolve product GTINs via `pyzbar` without invoking the Vision LLM when a valid barcode is present[cite: 3].
- [ ] Unstructured price-tag photos, listing URLs, and cross-border invoices parse into a validated `ExtractedItem` schema[cite: 3].

**Verification:**
- [ ] Tests pass: `pytest tests/test_capture_agent.py -v`
- [ ] Build succeeds: `ruff check src/agents/capture.py tests/test_capture_agent.py`
- [ ] Manual check: Pass a sample invoice string containing a real-format 16-digit card number and verify the logged LLM prompt contains `[REDACTED_PAN]`[cite: 2, 3].

**Dependencies:** Task 1, Task 7

**Files likely touched:**
- `src/agents/capture.py`
- `tests/test_capture_agent.py`

**Estimated scope:** Small (2 files)

---

## Task 9: Implement MarketAgent for eBay Browse API, Frankfurter FX, and Customs Lookup

**Description:** Implement `MarketAgent` (`src/agents/market.py`) to query comparable laptop listings across `EBAY_AU`, `EBAY_US`, and `EBAY_GB`, fetch mid-market FX rates from Frankfurter API, attach ID/AU customs parameters, and gracefully degrade to `data/market_fallback_cache.json` on network timeout or rate limit[cite: 3].

**Acceptance criteria:**
- [ ] `MarketAgent.fetch_comparables()` normalizes multi-country eBay listings into a list of `MarketOffer` models converted to target currency using live or cached FX rates[cite: 3].
- [ ] Network errors or missing eBay OAuth keys automatically fall back to `data/market_fallback_cache.json` with a `cache_hit: true` telemetry flag[cite: 3].
- [ ] Attaches applicable AU TRS and ID import duty rules from `data/customs_rules.json` based on buyer origin and destination[cite: 3].

**Verification:**
- [ ] Tests pass: `pytest tests/test_market_agent.py -v`
- [ ] Build succeeds: `ruff check src/agents/market.py tests/test_market_agent.py`
- [ ] Manual check: Run `MarketAgent` with network disabled and confirm it returns normalized comparable offers from the fallback cache in `< 50ms`[cite: 3].

**Dependencies:** Task 2, Task 7

**Files likely touched:**
- `src/agents/market.py`
- `tests/test_market_agent.py`

**Estimated scope:** Small (2 files)

---

## Checkpoint 3: After Tasks 7–9 (Ingestion, Telemetry & External Data Tools)
- [ ] All tests pass: `pytest tests/test_router_telemetry.py tests/test_capture_agent.py tests/test_market_agent.py -v`
- [ ] PII redaction, barcode extraction, and market comparable retrieval work both online and offline[cite: 2, 3].
- [ ] Review with human before proceeding to Phase 4.

---

## Task 10: Implement PlannerAgent and Deterministic AuditAgent Guardrail

**Description:** Implement `PlannerAgent` (`src/agents/planner.py`) to synthesize a financial action plan from `QuantVerdict` and user account balances, and `AuditAgent` (`src/agents/audit.py`) to enforce 100% numeric grounding against `QuantVerdict`, verify policy compliance, and assign Permission Tiers 0–3[cite: 2, 3].

**Acceptance criteria:**
- [ ] `PlannerAgent` produces a structured recommendation and narrative explanation strictly referencing numbers from `QuantVerdict`[cite: 3].
- [ ] `AuditAgent` extracts every float/integer token from the narrative, compares it against `QuantVerdict` within $10^{-2}$ tolerance, and replaces ungrounded prose with a deterministic verified template (0% numeric hallucination)[cite: 2, 3].
- [ ] `AuditAgent` enforces `permission_tier = 3` and `hard_block = True` whenever $S_{\text{scam}} \ge 0.85$[cite: 3].

**Verification:**
- [ ] Tests pass: `pytest tests/test_planner_audit.py -v --cov=src.agents.planner --cov=src.agents.audit`
- [ ] Build succeeds: `ruff check src/agents/planner.py src/agents/audit.py tests/test_planner_audit.py`
- [ ] Manual check: Inject a fabricated number (`"APR is 4.2%"` when `QuantVerdict.effective_apr_bnpl` is `0.184`) into `AuditAgent` and verify it flags the hallucination and outputs the corrected grounded figure[cite: 2, 3].

**Dependencies:** Task 5, Task 7

**Files likely touched:**
- `src/agents/planner.py`
- `src/agents/audit.py`
- `tests/test_planner_audit.py`

**Estimated scope:** Medium (3 files)

---

## Task 11: Implement Tiered ExecutionAgent and FastAPI Endpoints

**Description:** Implement `ExecutionAgent` (`src/agents/execution.py`) to enforce Permission Tiers 0–3 and HITL confirmation tokens before invoking `SandboxBankService`, and expose the full pipeline via FastAPI (`POST /api/v1/analyze`, `POST /api/v1/execute`, `GET /api/v1/trajectory/{trace_id}`, `GET /api/v1/account`) in `src/main.py`[cite: 2, 3].

**Acceptance criteria:**
- [ ] `POST /api/v1/analyze` runs `CaptureAgent` $\rightarrow$ `MarketAgent` $\rightarrow$ `QuantEngine` $\rightarrow$ `PlannerAgent` $\rightarrow$ `AuditAgent` and returns the complete analysis payload with a signed `hitl_challenge_token` for Tier 2–3 actions[cite: 2, 3].
- [ ] `POST /api/v1/execute` rejects Tier 2–3 requests missing a valid `hitl_confirmation_token` (`HTTP 403`) and rejects hard-blocked scam transactions (`HTTP 422`)[cite: 2, 3].
- [ ] Validated executions mutate the SQLite sandbox bank ledger and append the final transaction receipt to the trajectory log[cite: 1, 3].

**Verification:**
- [ ] Tests pass: `pytest tests/test_e2e_api.py -v`
- [ ] Build succeeds: `uvicorn src.main:app --check-config` (or startup smoke test via `TestClient`)
- [ ] Manual check: Execute a `POST /api/v1/analyze` followed by `POST /api/v1/execute` via `TestClient` and verify `/api/v1/trajectory/{trace_id}` returns all 5 agent steps[cite: 1, 2, 3].

**Dependencies:** Task 6, Task 8, Task 9, Task 10

**Files likely touched:**
- `src/agents/execution.py`
- `src/main.py`
- `tests/test_e2e_api.py`

**Estimated scope:** Medium (3 files)

---

## Checkpoint 4: After Tasks 10–11 (End-to-End Multi-Agent API & Security Gate)
- [ ] All backend unit and E2E API tests pass: `pytest tests/ -v --cov=src --cov-fail-under=90`
- [ ] OpenAPI schema at `/docs` validates cleanly and Permission Tiers 0–3 block unauthorized or fraudulent actions[cite: 1, 2, 3].
- [ ] Review with human before proceeding to Phase 5.

---

## Task 12: Build Responsive Web Client Capture and TrueCost Breakdown Views

**Description:** Scaffold the React + TypeScript + Tailwind CSS frontend (`web/`) with camera/barcode image upload, URL/invoice input, preset scenario selector (for 1-click judge testing), and the `QuantBreakdown` dashboard cards (Hedonic Fair Value, Robust Z-score, TOPSIS rank, Effective APR, 36m NPV TCO, Cross-Border Landed Cost, and 60-day Cash-Flow impact)[cite: 3].

**Acceptance criteria:**
- [ ] `CapturePanel.tsx` supports mobile browser camera capture (`accept="image/*" capture="environment"`), URL paste, and 3 one-click demo presets (BNPL Trap, Cross-Border Fair Deal, Scam Invoice)[cite: 3].
- [ ] `QuantBreakdown.tsx` renders all `QuantVerdict` metrics clearly alongside the current Sandbox Bank AUD/IDR balances[cite: 3].
- [ ] Frontend builds cleanly with zero TypeScript errors[cite: 2, 3].

**Verification:**
- [ ] Tests pass: `npm --prefix web run build`
- [ ] Build succeeds: `npm --prefix web run build`
- [ ] Manual check: Load the UI in a mobile-viewport browser and trigger each of the 3 preset scenarios against the FastAPI backend[cite: 3].

**Dependencies:** Task 11

**Files likely touched:**
- `web/package.json`
- `web/src/api.ts`
- `web/src/components/CapturePanel.tsx`
- `web/src/components/QuantBreakdown.tsx`
- `web/src/App.tsx`

**Estimated scope:** Medium (5 files)

---

## Task 13: Build Web Client Scam Alert, HITL Confirmation Modal, and Trajectory Drawer

**Description:** Complete the frontend interactive security and execution views: `ScamAlertBanner.tsx` (visualizing $S_{\text{scam}}$ probability and fraud flags), `HitlModal.tsx` (Tier 2–3 step-up confirmation dialog that submits `hitl_confirmation_token` to `/api/v1/execute`), and `TrajectoryViewer.tsx` (live AIEP multi-agent audit log drawer with JSON export button)[cite: 1, 2, 3].

**Acceptance criteria:**
- [ ] `HitlModal.tsx` displays exact transaction parameters, permission tier badge, and requires explicit user confirmation before calling `POST /api/v1/execute`[cite: 2, 3].
- [ ] `ScamAlertBanner.tsx` disables the payment button and displays a red hard-block state when $S_{\text{scam}} \ge 0.85$[cite: 3].
- [ ] `TrajectoryViewer.tsx` renders per-agent latency, model ID, numeric grounding audit status (`0 ungrounded numbers`), and allows downloading the trace as JSON[cite: 1, 2, 3].

**Verification:**
- [ ] Tests pass: `npm --prefix web run build`
- [ ] Build succeeds: `docker compose build`
- [ ] Manual check: Complete an end-to-end sinking-fund pot creation through `HitlModal` and verify the sandbox balance updates and `TrajectoryViewer` logs the execution[cite: 3].

**Dependencies:** Task 12

**Files likely touched:**
- `web/src/components/ScamAlertBanner.tsx`
- `web/src/components/HitlModal.tsx`
- `web/src/components/TrajectoryViewer.tsx`
- `web/vite.config.ts`

**Estimated scope:** Medium (4 files)

---

## Task 14: Implement 30-Case Benchmark Runner and Generate Compliance Artifacts

**Description:** Create the 30 labeled evaluation scenarios in `data/benchmark_cases.json`, write `scripts/run_benchmarks.py` to measure economic savings vs. naive baseline, numeric hallucination rate ($\pm$ `AuditAgent`), scam precision/recall, and p50/p95 latency, and generate the required submission documents (`docs/TECHNICAL_DOC.md`, `docs/SECURITY_ASSESSMENT.md`, `README.md`, and `docs/execution_evidence/`)[cite: 1, 2, 3].

**Acceptance criteria:**
- [ ] `python -m scripts.run_benchmarks` executes all 30 cases, writes `docs/benchmark_results.json` demonstrating **0.0% numeric hallucination with `AuditAgent`**, and exports sandbox operation logs to `docs/execution_evidence/`[cite: 1, 3].
- [ ] `docs/TECHNICAL_DOC.md` and `docs/SECURITY_ASSESSMENT.md` cover system architecture, core mathematical formulas, permission-tier implementation, and the known-risk register (Submission Checklist Items 1 & 5)[cite: 1, 3].
- [ ] `README.md` documents 1-command Docker deployment, environment setup, and test execution (Submission Checklist Item 4)[cite: 1, 3].

**Verification:**
- [ ] Tests pass: `pytest tests/ -v && python -m scripts.run_benchmarks`
- [ ] Build succeeds: `test -f docs/benchmark_results.json && test -f docs/TECHNICAL_DOC.md && test -f docs/SECURITY_ASSESSMENT.md`
- [ ] Manual check: Verify `docs/execution_evidence/` contains both simulated-account ledger logs and multi-agent trajectory JSONL files required by Submission Checklist Item 6[cite: 1, 3].

**Dependencies:** Task 11, Task 13

**Files likely touched:**
- `data/benchmark_cases.json`
- `scripts/run_benchmarks.py`
- `docs/TECHNICAL_DOC.md`
- `docs/SECURITY_ASSESSMENT.md`
- `README.md`

**Estimated scope:** Medium (5 files)

---

## Checkpoint 5: After Tasks 12–14 (Full Stack MVP, Benchmarks & Submission Bundle)
- [ ] All unit, guardrail, and E2E tests pass (`pytest` coverage $\ge 90\%$)[cite: 3].
- [ ] `docker compose up --build` serves the full application cleanly and passes all 3 live demo flows[cite: 2, 3].
- [ ] All code, benchmarks, security self-assessment, and execution evidence artifac