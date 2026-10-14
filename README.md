# TrueCost Autopilot — AI as a Financial Participant

**FinTechathon 2026 (Shenzhen International FinTech Competition)**  
*International AI Track · Topic A: Personal Finance Assistant*  
**Host Organization:** Shenzhen FinTech Competition Committee & WeBank  
**Theme:** *"AI as a Financial Participant"*

---

## 🏆 Project Overview

**TrueCost Autopilot** is an autonomous financial agent that acts as a true economic participant on behalf of consumers and international students. Instead of functioning as an ungrounded, passive conversational chatbot, TrueCost Autopilot operates under **cryptographically signed user mandates** (modeled after the Google Agent Payments Protocol / AP2).

The system continuously solves four critical financial pain points at the point of intent:
1. **Deconstructing Deceptive BNPL / "0% Installments":** An Internal Rate of Return (IRR) engine calculates the true Effective Annual Rate (EAR) and flags predatory debt traps.
2. **Cross-Border Landed Cost Calculation:** Dynamically computes destination import taxes (Indonesian Bea Cukai PPN/PPh rules), card FX spreads (2.5%), and tourist tax deductions (Australian TRS 10% refund).
3. **Finite-Horizon Optimal Stopping:** Determines whether to purchase immediately or wait for price drops using mathematical reservation price curves ($R_t$).
4. **Modified Z-Score Scam Intervention:** Detects extreme price anomalies ($M_i < -3.5$) and triggers a **Revolut-style Scam Intervention Flow** to halt Authorised Push Payment (APP) fraud before money leaves the bank.

---

## 📋 Competition Rule Compliance & Deliverables Checklist

This repository satisfies all required submission items under Section 5 of the Competition Rules (`international-topics-rules-en.docx`):

| Deliverable | Repository Path | Description & Status |
| :--- | :--- | :--- |
| **1. Technical Documentation** | [`docs/TECHNICAL_DOCUMENTATION.md`](docs/TECHNICAL_DOCUMENTATION.md) | Full system architecture, AIEP layering, core quant algorithms, and Ed25519 mandate design. |
| **2. Security Self-Assessment** | [`docs/SECURITY_SELF_ASSESSMENT.md`](docs/SECURITY_SELF_ASSESSMENT.md) | 4-tier permission model, STRIDE threat matrix, and known-risk ledger. |
| **3. Execution Evidence** | [`docs/EXECUTION_EVIDENCE.md`](docs/EXECUTION_EVIDENCE.md) & [`logs/sandbox_execution.jsonl`](logs/sandbox_execution.jsonl) | Simulated-account core banking ledger, sinking pot reservation logs, and cryptographic mandate verification trails. |
| **4. Source Code & Test Cases** | [`backend/`](backend/) & [`backend/tests/`](backend/tests/) | Pure deterministic quant modules, FastAPI REST endpoints, and 100% passing test suite. |
| **5. One-Click Deployment** | [`docker-compose.yml`](docker-compose.yml) & [`backend/Dockerfile`](backend/Dockerfile) | Production Docker environment containerizing the complete service. |

---

## 🚀 Quickstart & Reproduction Guide

### Prerequisites
- Python 3.11+ (or Docker Engine / Docker Desktop)
- `uv` (recommended) or standard `pip`

### Option 1: Native Local Setup (Fastest via uv)
```bash
# 1. Navigate to backend directory
cd backend

# 2. Create virtual environment and install dependencies
uv venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux / macOS:
source .venv/bin/activate

# 3. Install packages in editable mode with test dependencies
uv pip install -e . -e ".[dev]"

# 4. Run the full deterministic test suite
pytest -v

# 5. Launch the FastAPI development server
uvicorn app.main:app --reload --port 8000
```
API Documentation and interactive Swagger UI will be available at: `http://localhost:8000/docs`

### Option 2: One-Click Docker Deployment
```bash
# From the root directory:
docker compose up --build
```
Health check endpoint: `http://localhost:8000/health`

---

## 🧪 Deterministic Test Suite Verification

The core principle of TrueCost Autopilot is that **the AI model never performs financial arithmetic or security validation**. All calculations are handled by pure Python engines with zero LLM hallucination:

```bash
pytest -v
```

**Test Coverage Summary:**
- `tests/test_apr.py` — True 0% vs hidden admin fees, foregone cash discount opportunity costs, and predatory EAR thresholds.
- `tests/test_landed_cost.py` — Multi-currency conversion, FX spread markup, Indonesian customs valuation, and Australian TRS refunds.
- `tests/test_mandate_crypto.py` — Ed25519 cryptographic signing, canonical byte hashing, and adversarial tamper detection.
- `tests/test_scam_detector.py` — Boris Iglewicz and David Hoaglin Modified Z-Score ($M_i$), domain typosquatting, and scam intervention triggers.
- `tests/test_optimal_stopping.py` — Finite-horizon backward induction reservation price decay curve ($R_t$) and buy/wait evaluations.
- `tests/test_sandbox_bank.py` — Sinking pot fund reservation, disposable single-use virtual card tokenization, and rogue agent over-budget execution blocking.
- `tests/test_topsis.py` — Multi-criteria decision analysis ranking over hardware specifications.

---

## 🏗️ Architectural Invariants & Security Pillars

1. **Anti-Hallucination Invariant:** The LLM's role is restricted to semantic understanding and natural-language synthesis. Financial numbers are grounded deterministically by the quant engine and verified by the Audit Agent.
2. **Cryptographic Intent Mandates:** A user signs an Intent Mandate in the browser via Ed25519. The Core Bank independently verifies the signature chain before moving any funds.
3. **Revolut-Style Scam Intervention:** If an extreme statistical anomaly is detected, the transaction is locked by default, requiring an interactive cognitive friction override before any debit occurs.
4. **Disposable Virtual Cards:** Debits are settled using single-use virtual card numbers that self-destruct immediately upon clearing, eliminating credential theft risks.

---

## 📄 License
This project is submitted for the FinTechathon 2026 International Track under competition rules. All third-party libraries (FastAPI, PyNaCl, Cryptography, NumPy, SciPy) are standard permissible open-source software (MIT / Apache 2.0 / BSD).
