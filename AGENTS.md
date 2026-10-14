# Project: TrueCost Autopilot

## FinTechathon 2026 Official Rules Alignment
- **Track & Topic:** International AI Track — **Topic A: Personal Finance Assistant**
- **Theme:** *"AI as a Financial Participant"* (Autonomous execution within guardrails, not a passive chat wrapper)
- **Official Language:** English for all documentation, code, comments, commit messages, and presentation materials.
- **Deadline:** October 20, 2026, 23:59 Beijing Time (UTC+8) / 22:59 Jakarta Time (WIB).
- **Evaluation Criteria:**
  - Task Completion: **40%** (Full end-to-end sandbox execution, working proof-of-concept, simulated-account operation logs)
  - Security & Compliance: **30%** (Cryptographic Ed25519 mandates, permission tiers, bank-side re-verification, anti-scam interventions)
  - Innovation & Interaction: **30%** (AP2-inspired verifiable mandates, optimal-stopping buy timing, BNPL APR lie detector, landed-cost calculator)

## Submission Deliverables Checklist
1. `docs/TECHNICAL_DOCUMENTATION.md` — System architecture, core algorithm specifications, security design.
2. `docs/SECURITY_SELF_ASSESSMENT.md` — Permission-tier matrix, known risk ledger, threat model (STRIDE).
3. `docs/EXECUTION_EVIDENCE.md` + `logs/` — Sandbox bank transaction logs, exported signed mandate chains, replay audit trails.
4. `README.md` & `docker-compose.yml` — One-click reproduction, API OpenAPI docs, clean setup instructions.
5. `tests/` — Rigorous deterministic test suite covering math formulas, signature verification, and security bounds.
6. Presentation Deck (`presentation/`) & Demo Video script (`≤ 5 min`).

---

## Tech Stack
- **Backend:** Python 3.11+, FastAPI, Pydantic v2, SQLite / SQLModel (Sandbox Bank & Mandate Ledger)
- **Cryptography:** `cryptography` / `PyNaCl` (Ed25519 digital signatures for Intent & Cart Mandates)
- **Math & Statistics:** NumPy, SciPy (Deterministic quant engine: MAD robust z-scores, IRR/APR, TOPSIS, optimal stopping)
- **LLM Orchestration:** Modular Provider Adapter (Google Gemini / OpenAI / Anthropic with local/China-reachable fallback like Qwen/DeepSeek)
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS (Mobile-responsive web app with camera barcode/price-tag capture and in-browser Web Crypto Ed25519 signing)
- **Deployment:** Docker & Docker Compose (`docker compose up --build`)

---

## Core System Invariants & Boundaries (NEVER VIOLATE)

### 1. The Anti-Hallucination Invariant (Deterministic Math Only)
- **The LLM NEVER performs arithmetic or financial calculations.** All calculations (effective APR, true landed cost, robust z-score, reservation prices) MUST be executed by the deterministic Python `quant_engine` modules with 100% unit test coverage.
- The **Audit Agent** must verify that any number mentioned in user explanations matches the quant engine's exact output. If a hallucinated or ungrounded number is found, the response is blocked.

### 2. The Cryptographic Mandate Invariant (AP2 Inspired)
- No financial action can be executed without a cryptographically valid **Intent Mandate** signed by the user's private key (`Ed25519`).
- The **Sandbox Bank** independently verifies the user's signature, checks the expiration timestamp, validates the maximum budget cap, and enforces the merchant policy BEFORE executing any transfer or order.

### 3. Permission Tiers & Human-in-the-Loop (HITL)
- **Tier 0 (Read-Only):** Price checking, spec lookup, landed-cost calculation — Autonomous.
- **Tier 1 (Within Mandate & Low Risk):** Scheduled price-drop monitoring, reserve funds transfer to sinking pot — Autonomous.
- **Tier 2 (Binding Purchase Execution):** Issuing Cart Mandate and debiting payment within pre-signed bounds — Autonomous if within mandate bounds, or 1-tap confirmation if configured.
- **Tier 3 (Flagged / Anomaly / High Value):** Statistical anomaly (potential scam) or predatory BNPL detected — **MANDATORY Revolut-style Scam Intervention Flow** requiring user friction override.

### 4. Zero Data Retention & Privacy
- Sensitive user credentials (private keys, raw bank PINs) NEVER leave the client browser.
- External LLM prompts must mask any Personally Identifiable Information (PII).

---

## Code & Repo Conventions
- **Colocated Tests:** Every module in `backend/app/engine/` must have a corresponding test in `backend/tests/`.
- **Typing:** Strict typing throughout Python (`mypy` compliant) and TypeScript (`noImplicitAny`).
- **Audit Logging:** Every agent decision step, tool call, and bank transaction must be appended to an immutable JSONL trajectory log (`logs/agent_trajectory.jsonl`).
- **Clean Architecture:** Strict separation of layers:
  - `backend/app/api/` — FastAPI REST endpoints
  - `backend/app/agents/` — Intake, Market Watcher, Decision, Audit, Execution agents
  - `backend/app/engine/` — Pure deterministic quant modules (zero LLM dependencies)
  - `backend/app/bank/` — Sandbox bank state, accounts, orders, ledger, and mandate verification
  - `backend/app/schemas/` — Pydantic schemas (Mandate, Product, Transaction, AuditLog)
