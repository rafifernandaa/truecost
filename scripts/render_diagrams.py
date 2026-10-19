import urllib.request
import base64
import os
import json

diagrams = {
    'diagram_architecture.png': '''
graph TD
    classDef client fill:#EFF6FF,stroke:#2563EB,stroke-width:2px,color:#1E3A8A;
    classDef agent fill:#F5F3FF,stroke:#7C3AED,stroke-width:2px,color:#4C1D95;
    classDef quant fill:#ECFDF5,stroke:#059669,stroke-width:2px,color:#064E3B;
    classDef bank fill:#FFFBEB,stroke:#D97706,stroke-width:2px,color:#78350F;

    subgraph L1["1. Application and Client Interface Layer"]
        UI["Mobile-Responsive Web and Android Shell<br/>(Liquid Frosted Glass Design)"]:::client
        CRYPTO["In-Browser Web Crypto Engine<br/>(Ed25519 Private Key Stays on Device)"]:::client
        UI --> CRYPTO
    end

    subgraph L2["2. Agentic Workflow and Orchestration Layer"]
        INTAKE["Intake Agent<br/>(Semantic Intent Extraction and PII Redaction)"]:::agent
        WATCHER["Market Watcher Agent<br/>(Multi-Store Retail and Interbank FX Oracle)"]:::agent
        DECISION["Decision Agent<br/>(Timing, Landed Cost and TCO Synthesis)"]:::agent
        AUDIT["Audit Agent<br/>(Strict Numeric Groundedness Barrier)"]:::agent
        EXEC["Execution Agent<br/>(Signed Cart Mandate Assembly)"]:::agent

        CRYPTO -->|"Signed Intent Mandate (Ed25519)"| INTAKE
        INTAKE --> WATCHER
        WATCHER --> DECISION
        DECISION --> AUDIT
        AUDIT -->|"Strictly Grounded Output"| EXEC
    end

    subgraph L3["3. Pure Deterministic Quant Engine (Zero LLM Math)"]
        LC["Cross-Border Landed Cost<br/>(Customs, PPN 11%, PPh 7.5%, FX Spread)"]:::quant
        APR["BNPL Lie Detector / IRR<br/>(Newton-Raphson Effective APR and EAR)"]:::quant
        OPP["Opportunity Cost Engine<br/>(Rule of 72 and Life Energy Hours)"]:::quant
        STOP["Optimal Stopping Engine<br/>(Robbins-Siegmund Reservation Price)"]:::quant
        SCAM["Scam Detector and Invoice Audit<br/>(MAD Robust Z-Score, GSTIN, IMEI Luhn)"]:::quant
        TOP["TOPSIS Multi-Criteria Ranker<br/>(Relative Closeness to Ideal Spec)"]:::quant

        DECISION <--> LC
        DECISION <--> APR
        DECISION <--> OPP
        DECISION <--> STOP
        DECISION <--> SCAM
        DECISION <--> TOP
    end

    subgraph L4["4. Core Banking, Ledger and Payment Rails"]
        VERIF["Independent Mandate Verifier<br/>(Ed25519 Signature, Nonce and Expiry)"]:::bank
        ESCROW["Sinking Pot Vault<br/>(Ring-Fenced Budget Reservation)"]:::bank
        VCARD["Single-Use Virtual Card<br/>(Exact-Cap Token and Atomic Clearance Burn)"]:::bank
        LEDGER["Double-Entry Core Ledger<br/>(Integer Minor Units and Immutable Triggers)"]:::bank
        RAILS["Indonesian Payment Rails<br/>(Xendit Callback HMAC and Midtrans SHA-512)"]:::bank

        EXEC -->|"Dispatches Signed Cart Mandate"| VERIF
        VERIF -->|"Valid Signature and Bounds Pass"| ESCROW
        ESCROW --> VCARD
        VCARD --> LEDGER
        RAILS <--> LEDGER
    end
''',
    'diagram_mandate_lifecycle.png': '''
sequenceDiagram
    autonumber
    actor User as User (Client Device)
    participant Agent as Agent Pipeline
    participant Quant as Quant Engine
    participant Bank as Core Sandbox Bank
    participant Merchant as Retail Merchant

    User->>User: Generate Ed25519 Keypair (Web Crypto)
    User->>Agent: Submit Query + Sign Intent Mandate
    Agent->>Bank: Register Intent Mandate and Lock Sinking Pot
    Bank-->>Agent: Sinking Pot Locked (Budget Ringfenced)
    Agent->>Quant: Evaluate Landed Cost, Effective APR and Timing
    Quant-->>Agent: Pure Deterministic Results (0 LLM Math)
    Agent->>Agent: Audit Agent Verifies Numeric Groundedness
    Agent->>Agent: Execution Agent Signs Cart Mandate (Ed25519)
    Agent->>Bank: Dispatch Signed Cart Mandate
    Bank->>Bank: Independently Verify Signature, Expiry and Budget Cap
    Bank->>Bank: Generate Single-Use Virtual Card (Exact-Cap Token)
    Bank->>Merchant: Atomic Clearance and Settlement
    Merchant-->>Bank: Settlement Confirmed
    Bank->>Bank: Instantly Burn Virtual Card (Status: DESTROYED)
    Bank->>Bank: Post Balanced Double-Entry Minor-Unit Entries
    Bank->>User: Return Surplus Sinking Pot Funds to Checking
''',
    'diagram_invoice_scam_audit.png': '''
flowchart LR
    classDef input fill:#EFF6FF,stroke:#2563EB,stroke-width:2px,color:#1E3A8A;
    classDef check fill:#F5F3FF,stroke:#7C3AED,stroke-width:2px,color:#4C1D95;
    classDef pass fill:#ECFDF5,stroke:#059669,stroke-width:2px,color:#064E3B;
    classDef fail fill:#FEF2F2,stroke:#DC2626,stroke-width:2px,color:#991B1B;

    INV["Retail Invoice / Bill Copy<br/>(Image / OCR Text Input)"]:::input

    subgraph FORENSIC ["Deterministic Forensic Checks"]
        TAX["Statutory Tax IDs<br/>- India GSTIN Format and PAN<br/>- Australia ABN Mod-89<br/>- Indonesia NPWP (15/16-digit)"]:::check
        IRN["Govt E-Invoice Seal<br/>- 64-char SHA-256 IRN Hash"]:::check
        IMEI["Hardware IMEI<br/>- 15-digit 3GPP/GSM Mod-10 Luhn"]:::check
        MATH["Cent/Paisa Balance<br/>|Taxable + Tax + Ship - Disc - Total| <= 0.01"]:::check
        ZMAD["Boris Iglewicz and David Hoaglin<br/>Modified Z-Score MAD < -3.5"]:::check
    end

    INV --> TAX
    INV --> IRN
    INV --> IMEI
    INV --> MATH
    INV --> ZMAD

    SCORE{"Weighted Authenticity<br/>Scoring Engine"}

    TAX --> SCORE
    IRN --> SCORE
    IMEI --> SCORE
    MATH --> SCORE
    ZMAD --> SCORE

    SAFE["VERIFIED AUTHENTIC<br/>Score >= 0.85<br/>Autonomous Settlement Allowed"]:::pass
    SCAM["COUNTERFEIT / SCAM ALERT<br/>Score < 0.60 or Failed Invariant<br/>Mandatory Revolut-Style Intervention"]:::fail

    SCORE -->|"Passes All Checks"| SAFE
    SCORE -->|"Mismatch / Anomaly Detected"| SCAM
'''
}

os.makedirs('docs/diagrams', exist_ok=True)
for filename, code in diagrams.items():
    encoded = base64.urlsafe_b64encode(code.strip().encode('utf-8')).decode('utf-8')
    url = f'https://mermaid.ink/img/{encoded}?bgColor=FFFFFF'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    target_path = os.path.join('docs/diagrams', filename)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
            with open(target_path, 'wb') as f:
                f.write(data)
            print(f'Rendered {filename}: {len(data)} bytes')
    except Exception as e:
        print(f'Failed {filename}: {e}')
