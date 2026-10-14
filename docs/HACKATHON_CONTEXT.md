# FinTechathon 2026 — International Track: Context Brief

> Single source of truth for the agent and the team. Consolidated from
> `international-topics-rules-en.docx` (OFFICIAL) and `Additional Information.txt`
> (team notes from WeBank Technical Open Class sessions 1 & 2). Where they conflict, the docx wins.

## Theme
**"AI as a Financial Participant"** — an AI agent that *completes real tasks* in a financial scenario.
Not a chat wrapper. Single-LLM prompt wrappers are explicitly said to be eliminated.

## Topics (pick ONE)
| | Topic | Core scope |
|---|---|---|
| A | Personal Finance Assistant | budgeting, bill analysis, spending insights, actionable recs |
| B | Wealth Advisory Agent | product comparison, risk profiling, compliant + explainable allocation |
| C | Cross-border & Student Finance | remittance, tuition payments, credit building, multi-currency |
| D | Insurance Assistant | policy Q&A, coverage-gap analysis, claims guidance |
| E | SME Finance Copilot | financing matching, cash-flow mgmt & alerts, business analysis |
| F | Agent Wallet (on-chain) | autonomous on-chain ops; **+0–5 challenge bonus** |

## Scoring (identical across topics)
- **Task completion — 40%**
- **Security & compliance — 30%**
- **Innovation & interaction — 30%**
- On-chain challenge bonus — 0–5 pts (Topic F only)

## Hard deadline
**Oct 20, 2026 23:59 Beijing (UTC+8) = Oct 20 22:59 WIB (UTC+7).** Registration + submission share the deadline.
Latest upload wins; nothing accepted after.

## Submission checklist (all mandatory unless noted)
1. Technical documentation — system architecture, core algorithm description, security design
2. Presentation deck — final talk ≤ 10 min
3. Demo video — optional, ≤ 5 min (but execution evidence for non-on-chain topics expects a demo video)
4. Source code — README, GitHub link, deployment instructions, **test cases**
5. **Security self-assessment report** — permission-tier implementation + known-risk list
6. **Execution evidence** — non-on-chain: simulated-account/sandbox operation logs + demo video; on-chain: real tx hashes

## Eligibility
- Full-time students at overseas (non-China, incl. non-HK/Macao/Taiwan) universities
- Teams of **2–5**; **≥ 60% non-Chinese nationals**; one team per person across tracks
- English only

## Timeline
Oct 21 compliance screening → late Oct online review (WeBank experts + scholars) → Oct 31 finalists →
Nov 20 check-in + WeBank HQ visit → Nov 21–23 Grand Final, Shenzhen (≥1 member in person; travel + hotel covered).

## Prizes (International Track, RMB, pre-tax)
1st 100k · 2nd 80k · 3rd 50k · Best Innovation 20k · Excellence Awards (several) · fast-track WeBank interviews.

## What judges said they want (Technical Open Class notes)
- **Real financial pain point** with business/commercial value in digital banking; no generic AI.
- **Multi-agent architecture with clear roles**: Planner → Execution/Tool → Validation/Audit.
- **AIEP layering**: Data & Infra · Model Matrix · Agentic Workflow/Tools · Application.
- **Deterministic validation / guardrails** so numbers and tool calls never hallucinate.
- **Trustworthy AI**: PII masking/encryption, explainability, **agent execution trajectory logs**, **human-in-the-loop** above risk/amount thresholds.
- **Working end-to-end prototype**, live-executable, not hardcoded; Docker; API spec.
- **Benchmark vs. conventional/baseline method.**
- **Compute efficiency**: latency, small/efficient models preferred over big slow ones.
- International plus: cross-border, multi-language, multi-jurisdiction regulation.

## Known conflict
Team notes say Directions C/F get higher relevance for the International Track; the official docx says topic
choice does not affect scoring (except the on-chain bonus). Treat C/F as a *soft* preference, not a rule.

## Integrity / IP
Original work; all third-party data/code/OSS must be properly licensed. IP stays with team.
