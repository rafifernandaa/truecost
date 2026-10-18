Data & Infrastructure Layer: SQLite 3 (WAL mode) transactional sandbox bank, data/laptop_reference_500.csv (curated spec dataset for Hedonic regression), data/customs_rules.json (AU TRS and ID customs thresholds), and data/market_fallback_cache.json (offline resilience cache).   
TXT
+ 1

Model Matrix Layer (LLMRouter): Provider-agnostic adapter supporting Alibaba Cloud DashScope (qwen-vl-max, qwen2.5-14b-instruct) and DeepSeek (deepseek-chat) for low-latency Mainland China execution during the Shenzhen finals, alongside Google Gemini (gemini-2.5-flash) for local development[cite: 2, 3].

Agentic Workflow & Middle Tools Layer: Five specialized agents (CaptureAgent, MarketAgent, PlannerAgent, AuditAgent, ExecutionAgent) bound by strict Pydantic v2 schemas and connected to the deterministic QuantEngine[cite: 2, 3].

Application Layer: FastAPI REST backend with OpenAPI 3.1 documentation and a responsive React + Tailwind CSS web client[cite: 2, 3].

5. Deterministic Quantitative Engine Specifications (src/quant/)
All mathematical and statistical methods execute in deterministic Python (numpy, scipy, scikit-learn).   
MD

5.1 Price Fairness & Empirical Wait Signal
Robust Z-Score (Median / MAD): Given comparable prices 
P={p 
1
​
 ,…,p 
n
​
 } in target currency:
   
MD

M=median(P),MAD=median(∣p 
i
​
 −M∣),Z 
robust
​
 (p 
∗
 )= 
MAD+10 
−9
 
0.6745⋅(p 
∗
 −M)
​
 
Real Discount Verification: Compares seller's claimed reference/"was" price 
p 
claimed
​
  against observed 90-day median history 
M 
hist
​
  to expose artificial price anchoring.   
MD

Buy-Now vs. Wait Probability: Computes empirical probability of a price drop exceeding 
k% within 
N days from historical price series: 
P
^
 (min 
τ∈[1,N]
​
 P 
t+τ
​
 ≤(1−k)P 
t
​
 ).   
MD

5.2 Spec-Adjusted Hedonic Pricing & TOPSIS Ranking
Hedonic Ridge Regression: Pre-fitted on standardized hardware vectors 
x=[1,ln(CPU 
mark
​
 ),ln(GPU 
mark
​
 +1),ln(RAM 
GB
​
 ),ln(SSD 
GB
​
 ),Weight 
kg
​
 ,OLED 
flag
​
 ] 
T
  with 
ℓ 
2
​
  penalty 
λ=1.0:
   
MD

β
^
​
 =(X 
T
 X+λI) 
−1
 X 
T
 ln(P), 
p
^
​
  
hedonic
​
 =exp(x 
∗T
  
β
^
​
 ),Residual=p 
∗
 − 
p
^
​
  
hedonic
​
 
TOPSIS Multi-Criteria Comparison: Normalizes candidate matrix 
X 
ij
​
  across cost criteria (Landed Cost, 36m TCO) and benefit criteria (CPU score, RAM, Warranty, Seller Trust), applies user/entropy weights 
w 
j
​
 , and ranks offers by relative closeness to ideal solution 
C 
i
∗
​
 = 
D 
i
+
​
 +D 
i
−
​
 
D 
i
−
​
 
​
 ∈[0,1].   
MD

5.3 Payment Method Effective APR, NPV TCO & Cross-Border Landed Cost
Effective APR via IRR (scipy.optimize.brentq): Solves monthly discount rate 
r 
m
​
  equating upfront cash price (net of card cashback 
r 
cb
​
 ) to BNPL/installment cash flows 
CF 
t
​
  (incorporating origination fees, monthly account fees, and FX spread markups):
   
MD

CF 
0
​
 −P 
0
​
 (1−r 
cb
​
 )+ 
t=1
∑
T
​
  
(1+r 
m
​
 ) 
t
 
CF 
t
​
 
​
 =0⟹APR 
eff
​
 =(1+r 
m
​
 ) 
12
 −1
Total Cost of Ownership (NPV over 
H=36 Months): Discounts monthly energy consumption 
E 
t
​
 , expected warranty/consumables 
M 
t
​
 , and terminal resale value 
R 
H
​
 =P 
0
​
 (1−δ) 
H/12
  at monthly opportunity rate 
d 
m
​
 [cite: 3]:

TCO 
NPV
​
 =P 
landed
​
 + 
t=1
∑
H
​
  
(1+d 
m
​
 ) 
t
 
E 
t
​
 +M 
t
​
 
​
 − 
(1+d 
m
​
 ) 
H
 
R 
H
​
 
​
 
Cross-Border Landed Cost (ID 
↔ AU):

P 
landed
​
 =(P 
foreign
​
 −TRS 
refund
​
 )⋅S 
mid
​
 ⋅(1+s 
FX
​
 )+C 
ship
​
 +Duty(P 
CIF
​
 )+VAT(P 
CIF
​
 +Duty)

Applies the Australian Tourist Refund Scheme (
TRS 
refund
​
 = 
11
P 
AUD
​
 
​
  when 
P 
AUD
​
 ≥300 AUD at a single ABN retailer) and Indonesian customs duty/import tax rules[cite: 3].

5.4 Budget-Envelope Impact & Composite Fraud Scoring
60-Day Cash-Flow Projection: Simulates daily balance trajectory 
B 
t
​
 =B 
t−1
​
 +Inc 
t
​
 −Fix 
t
​
 −μ 
disc
​
 −Outflow 
t
​
  for 
t∈[1,60] and triggers a liquidity alert if 
min 
t
​
 B 
t
​
 <B 
buffer
​
 [cite: 3].

Scam & Invoice Fraud Probability: Combines low-side price anomaly 
max(0,−Z 
robust
​
 −1.8), Empirical Bayes seller trust 
Trust 
Bayes
​
 = 
n 
total
​
 +10
n 
pos
​
 +8
​
 , invoice IBAN/domain mismatch 
I 
IBAN
​
 , and off-platform payment demand 
I 
wire
​
 [cite: 3]:

S 
scam
​
 =σ(−2.2+1.4max(0,−Z 
robust
​
 −1.8)+2.5(1−Trust 
Bayes
​
 )+3.0I 
IBAN
​
 +2.0I 
wire
​
 )
6. Security, Compliance & Trustworthy AI Design (30% Rubric Weight)
Pre-LLM PII Redaction (CaptureAgent): Deterministic regex + Luhn check masks credit/debit card numbers, passport/NIK numbers, phone numbers, emails, and residential addresses before any payload reaches an external LLM[cite: 2, 3].

Zero Numeric Hallucination Gate (AuditAgent): Extracts all numeric values from PlannerAgent prose and verifies exact correspondence (
±10 
−2
  rounding tolerance) against QuantVerdict fields[cite: 2, 3]. Any ungrounded number is blocked and replaced via deterministic template rendering[cite: 2, 3].

Permission-Tier Enforcement & HITL Matrix (ExecutionAgent):

Tier 0 (Read-Only): Query prices, compute quant metrics, read balances — Auto-executed[cite: 3].

Tier 1 (Advisory): Save comparison, set passive price alert — Auto-executed + logged[cite: 3].

Tier 2 (Bounded Mutation): Open sinking-fund pot, schedule transfer 
≤200 AUD, place conditional buy-if-price-below-X escrow order — Requires 1-click HITL confirmation token[cite: 1, 2, 3].

Tier 3 (High-Risk / Outflow / Scam-Flagged): Execute immediate card/cross-border payment 
>200 AUD, accept BNPL contract, or transact with 
0.60≤S 
scam
​
 <0.85 — Requires explicit HITL step-up confirmation + risk acknowledgment; hard-blocked if 
S 
scam
​
 ≥0.85[cite: 1, 2, 3].

Immutable Trajectory Log: Appends structured JSONL records (trace_id, timestamp_utc, agent, model_id, input_hash, quant_verdict, audit_passed, permission_tier, hitl_token_hash, latency_ms, tokens) for every step, exported to docs/execution_evidence/[cite: 1, 2, 3].

7. Tech Stack, Commands & Project Structure
7.1 Tech Stack
Backend: Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2.0, SQLite 3 (WAL mode)[cite: 3]

Quant & Vision: numpy, scipy, pandas, scikit-learn, pyzbar, Pillow

[cite: 3]

LLM Providers: openai SDK (configured for Alibaba DashScope Qwen & DeepSeek), google-genai SDK (Gemini)[cite: 3]

Frontend: React 18, TypeScript, Vite, Tailwind CSS[cite: 3]

Deployment: Docker & Docker Compose[cite: 2, 3]

7.2 Standard Commands
Bash
# Install dependencies
uv venv .venv && source .venv/bin/activate
uv pip install -r requirements.txt

# Seed sandbox bank & fit hedonic model
python -m src.sandbox_bank.seed

# Run unit, guardrail, and integration tests
pytest tests/ -v --cov=src --cov-report=term-missing --cov-fail-under=90

# Run 30-case evaluation benchmark & export execution evidence
python -m scripts.run_benchmarks --cases data/benchmark_cases.json --output docs/benchmark_results.json

# Launch containerized full stack
docker compose up --build
7.3 Directory Layout
Plaintext
truecost/
├── data/
│   ├── laptop_reference_500.csv       # Curated laptop dataset for Hedonic regression
│   ├── customs_rules.json             # Official ID Import Duty/VAT & AU GST/TRS rules
│   ├── market_fallback_cache.json     # Cached eBay & FX payloads for live demo reliability
│   └── benchmark_cases.json           # 30 test cases (fair deal, BNPL trap, cross-border, scam)
├── src/
│   ├── config.py                      # Environment variables & Model Matrix settings
│   ├── quant/
│   │   ├── pricing.py                 # Robust Z-score, Hedonic Ridge, TOPSIS
│   │   ├── finance.py                 # IRR/APR solver, NPV TCO, Landed Cost, 60-day cash flow
│   │   └── fraud.py                   # Bayesian seller trust & scam/invoice fraud scorer
│   ├── agents/
│   │   ├── schemas.py                 # Pydantic v2 contracts
│   │   ├── router.py                  # Provider-agnostic LLM Matrix (Qwen / DeepSeek / Gemini)
│   │   ├── capture.py                 # Barcode decode, PII redaction, Vision-LLM OCR
│   │   ├── market.py                  # eBay Browse API, Frankfurter FX, customs rule lookup
│   │   ├── planner.py                 # Financial decision synthesizer
│   │   ├── audit.py                   # Numeric grounding verifier & policy gate
│   │   └── execution.py               # Permission Tier 0-3 enforcement & sandbox bank caller
│   ├── sandbox_bank/
│   │   ├── models.py                  # SQLite schema (accounts, cards, pots, orders, ledger)
│   │   ├── service.py                 # Idempotent ACID banking transactions
│   │   └── seed.py                    # Initial student persona account & BNPL seed
│   ├── telemetry/
│   │   └── trajectory.py              # Append-only JSONL trajectory logger
│   └── main.py                        # FastAPI entrypoint
├── web/                               # Responsive React + Tailwind frontend
├── scripts/
│   └── run_benchmarks.py              # Reproducible benchmark runner
├── tests/                             # Unit, security guardrail, and E2E test suites
├── docs/
│   ├── TECHNICAL_DOC.md               # Submission Item 1: Architecture, core algos, security
│   ├── SECURITY_ASSESSMENT.md         # Submission Item 5: Permission tiers & known-risk list
│   └── execution_evidence/            # Submission Item 6: Sandbox operation logs & traces
├── docker-compose.yml
└── README.md                          # Submission Item 4: Deployment & test guide
8. Explicit "Not Doing" Scope Boundaries
Physical Counterfeit Banknote Scanning: Smartphone RGB sensors cannot capture UV, IR, or magnetic ink security features, counterfeit currency datasets are restricted, and physical cash inspection falls outside all six FinTechathon topics.   
DOCX
+ 1

Enterprise/SME Three-Way Invoice Matching: Full ERP accounts-payable automation belongs to Topic E (SME Finance Copilot) and would split focus from the consumer/student cross-border flow; invoice checks are scoped strictly to student/consumer payment fraud signals.   
DOCX
+ 1

Unauthorized Marketplace Scraping: Scraping HTML from Tokopedia, Shopee, or Amazon violates Terms of Service and jeopardizes the 30% Security & Compliance score; only official APIs (eBay Browse API, Frankfurter FX) and clearly labeled reference datasets are used[cite: 1, 2, 3].

Live Real-Money Payment Rails: Competition rules explicitly accept simulated-account/sandbox operation logs for non-on-chain topics[cite: 1, 3].

Unbounded Product Categories: Restricted to laptops for the MVP so hedonic regression operates on a coherent, standardized hardware feature space[cite: 3].

Topic F On-Chain Wallet Integration: Carries at most a 0–5 point bonus while diverting critical engineering time away from the core 100-point rubric[cite: 1, 3].

9. Sprint Schedule & Submission Checklist (Deadline: Oct 20, 2026, 22:59 WIB)
Date	Milestone	Deliverables
Oct 14–15	Foundation & Quant Core	
Repo + Docker skeleton, laptop_reference_500.csv, customs_rules.json, sandbox-bank SQLite schema, LLMRouter adapter[cite: 3]

Oct 16	Ingestion & Market Tools	
CaptureAgent (barcode + Vision OCR + PII masking) & MarketAgent (eBay Browse API + FX + fallback cache)[cite: 3]

Oct 17	Deterministic Quant Engine	
pricing.py, finance.py, fraud.py + 100% unit test coverage across all formulas[cite: 3]

Oct 18	Agents, Guardrails & UI	
PlannerAgent, AuditAgent, ExecutionAgent, Permission Tiers 0–3, HITL modal, Trajectory Viewer, React UI wiring[cite: 3]

Oct 19	Benchmarks & Compliance Docs	
Run 30-case benchmark suite; finalize TECHNICAL_DOC.md (#1) and SECURITY_ASSESSMENT.md (#5)[cite: 1, 3]

Oct 20	Final Packaging & Upload	
Presentation deck ≤10 min (#2), demo video ≤5 min (#3), GitHub repo (#4), execution_evidence/ (#6); submit by 18:00 WIB

[cite: 1, 3]