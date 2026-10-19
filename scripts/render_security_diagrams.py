import urllib.request
import base64
import os

security_diagrams = {
    'security_tiers.png': '''
flowchart TD
    classDef t0 fill:#EFF6FF,stroke:#2563EB,stroke-width:2px,color:#1E3A8A;
    classDef t1 fill:#ECFDF5,stroke:#059669,stroke-width:2px,color:#064E3B;
    classDef t2 fill:#FEF3C7,stroke:#D97706,stroke-width:2px,color:#78350F;
    classDef t3 fill:#FEF2F2,stroke:#DC2626,stroke-width:2px,color:#991B1B;

    REQ["Incoming Financial or Agent Action"]

    REQ --> C0{"Is action read-only?<br/>(Price check, FX query, TCO)"}
    C0 -->|"Yes"| T0["Tier 0: Observational<br/>- Autonomous Execution: YES<br/>- Crypto Gate: None<br/>- Audit: Ephemeral Query Log"]:::t0

    C0 -->|"No"| C1{"Is action internal fund reserve?<br/>(Sinking pot, price trigger)"}
    C1 -->|"Yes"| T1["Tier 1: Internal Allocation<br/>- Autonomous Execution: YES<br/>- Crypto Gate: Valid Ed25519 Intent Mandate<br/>- Audit: Reversible Transfer to Checking"]:::t1

    C1 -->|"No"| C2{"Is purchase within bounds and safe?<br/>(Budget cap, APR safe, low scam score)"}
    C2 -->|"Yes"| T2["Tier 2: Compliant Settlement<br/>- Autonomous Execution: YES<br/>- Crypto Gate: Intent + Cart Mandate Verified<br/>- Audit: Single-Use Disposable Card Destroyed"]:::t2

    C2 -->|"No"| C3{"Anomaly Detected?<br/>(Z-Score anomaly, Predatory BNPL,<br/>Fake Invoice, Off-Platform Wire)"}
    C3 -->|"Yes"| T3["Tier 3: High-Risk Scam Alert<br/>- Autonomous Execution: HARD HALT<br/>- Crypto Gate: Step-Up Diagnostic Quiz<br/>- Friction: Mandatory 60s Cognitive Cooldown"]:::t3
''',
    'security_boundaries.png': '''
flowchart LR
    classDef client fill:#EFF6FF,stroke:#2563EB,stroke-width:2px,color:#1E3A8A;
    classDef isolated fill:#FEF2F2,stroke:#DC2626,stroke-width:2px,color:#991B1B;
    classDef agent fill:#F5F3FF,stroke:#7C3AED,stroke-width:2px,color:#4C1D95;
    classDef quant fill:#ECFDF5,stroke:#059669,stroke-width:2px,color:#064E3B;
    classDef bank fill:#FFFBEB,stroke:#D97706,stroke-width:2px,color:#78350F;

    subgraph CLIENT ["Client Device (Browser Sandbox)"]
        KEY["Ed25519 Private Key<br/>(Web Crypto Subsystem)<br/>NEVER LEAVES BROWSER"]:::client
        SIGN["Mandate Signer"]:::client
        KEY --> SIGN
    end

    subgraph UNTRUSTED ["Untrusted External Environment"]
        ROGUE["Rogue Merchants<br/>Prompt Injection Attacks<br/>Counterfeit Invoices"]:::isolated
    end

    subgraph AGENT_LAYER ["Orchestration Layer"]
        PII["PII Redaction Barrier<br/>(Masks PAN, NIK, Email)"]:::agent
        LLM["LLM Semantic Parser<br/>(ZERO DB / PAYMENT ACCESS)"]:::agent
        AUDIT["Audit Agent<br/>(Numeric Grounding Verifier)"]:::agent
        PII --> LLM --> AUDIT
    end

    subgraph QUANT_LAYER ["Deterministic Quant Engine"]
        MATH["Pure Python Math<br/>(100 percent Deterministic<br/>NumPy / SciPy)"]:::quant
    end

    subgraph BANK_LAYER ["Sandbox Core Banking and Ledger"]
        GATE["Independent Mandate Verifier<br/>(Ed25519 Signature, Budget Cap)"]:::bank
        CARDS["Single-Use Card Mint<br/>(Atomic Clearance Burn)"]:::bank
        LEDGER["Immutable Double-Entry Ledger<br/>(Integer Minor Units)"]:::bank
        GATE --> CARDS --> LEDGER
    end

    ROGUE -.->|"Untrusted Input"| PII
    SIGN -->|"Signed Intent Mandate"| PII
    LLM <--> MATH
    AUDIT -->|"Strictly Bounded Payload"| GATE
'''
}

os.makedirs('docs/diagrams', exist_ok=True)
for filename, code in security_diagrams.items():
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
