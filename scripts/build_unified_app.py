import re
import os

def create_unified_html():
    with open("stitch_output/f362326752ab4e7b8a0797da9f50fc40.html", "r", encoding="utf-8") as f:
        html1 = f.read()
    with open("stitch_output/c967f13527324ad591b2b39d38db0fd1.html", "r", encoding="utf-8") as f:
        html2 = f.read()
    with open("stitch_output/9ece5206870b40fabc05bca5533a4fe2.html", "r", encoding="utf-8") as f:
        html3 = f.read()
    with open("stitch_output/fdb14843450b47bb9f1317cd20b6f554.html", "r", encoding="utf-8") as f:
        html4 = f.read()

    # Extract <main> content from each
    def extract_main(html):
        m = re.search(r"<main[^>]*>(.*?)</main>", html, re.DOTALL)
        return m.group(1) if m else ""

    main1 = extract_main(html1)
    main2 = extract_main(html2)
    main3 = extract_main(html3)
    main4 = extract_main(html4)

    # We will build an index.html with:
    # 1. Shared Head with Tailwind, Fonts, Material Symbols
    # 2. Shared Header with TrueCost Edition 26 and dual currency
    # 3. 4 Main sections (tab-section-capture, tab-section-verdict, tab-section-shield, tab-section-audit)
    # 4. Master dynamic morphing dock that controls switching between them
    # 5. Connected event listeners:
    #    - Preset 01 (BNPL) -> updates inputs, switches to Verdict
    #    - Preset 02 (AU Tax) -> updates inputs, switches to Verdict
    #    - Preset 03 (Scam) -> switches to Shield
    #    - Analyze button -> switches to Verdict
    #    - ACTIVATE SHIELD button -> switches to Shield
    #    - HITL Confirm button -> executes and switches to Audit
    #    - Dynamic dock tabs -> switches to respective section

    unified_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover"/>
  <title>TrueCost Autopilot</title>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin=""/>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@300;500;700&display=swap" rel="stylesheet"/>
  <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet"/>
  <script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
  <script>
    tailwind.config = {{
      darkMode: "class",
      theme: {{
        extend: {{
          colors: {{
            "primary": "#00288e",
            "primary-container": "#1e40af",
            "on-primary": "#ffffff",
            "secondary": "#a73a0a",
            "secondary-container": "#ff7947",
            "tertiary": "#003d2c",
            "tertiary-container": "#00563f",
            "background": "#fcf9f6",
            "surface": "#fcf9f6",
            "on-surface": "#1c1c1a",
            "on-surface-variant": "#444653",
            "surface-container-high": "#ebe8e5",
            "surface-container-highest": "#e5e2e0"
          }},
          fontFamily: {{
            "body-md": ["Inter", "sans-serif"],
            "headline-lg": ["Space Grotesk", "sans-serif"],
            "headline-md": ["Space Grotesk", "sans-serif"],
            "label-caps": ["Space Grotesk", "sans-serif"],
            "numeral-display": ["Space Grotesk", "sans-serif"],
            "index-marker": ["Space Grotesk", "sans-serif"]
          }}
        }}
      }}
    }};
  </script>
  <style>
    @layer base {{
      html, body {{
        width: 100vw;
        margin: 0;
        padding: 0;
        background-color: #fcf9f6;
        overscroll-behavior: none;
        -webkit-font-smoothing: antialiased;
      }}
      .pb-safe {{ padding-bottom: env(safe-area-inset-bottom, 16px); }}
      .pt-safe {{ padding-top: env(safe-area-inset-top, 8px); }}
    }}
    ::-webkit-scrollbar {{ display: none; }}
    .dock-spring {{
      transition: all 340ms cubic-bezier(0.4, 0, 0.2, 1);
    }}
    .tab-section {{
      display: none;
      animation: fadeIn 0.25s ease-out forwards;
    }}
    .tab-section.active {{
      display: block;
    }}
    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(6px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
  </style>
</head>
<body class="bg-gradient-to-br from-amber-50/70 via-orange-50/40 via-sky-50/50 to-stone-100 text-slate-800 font-body-md text-sm min-h-screen flex flex-col relative overflow-x-hidden antialiased">

  <!-- Ambient Decorative Background Glows -->
  <div class="fixed inset-0 pointer-events-none z-0 overflow-hidden">
    <div class="absolute -top-24 -left-20 w-96 h-96 rounded-full bg-gradient-to-br from-amber-200/50 via-orange-200/40 to-transparent blur-3xl"></div>
    <div class="absolute top-1/4 -right-24 w-96 h-96 rounded-full bg-gradient-to-bl from-sky-200/50 via-teal-100/40 to-transparent blur-3xl"></div>
    <div class="absolute bottom-20 left-10 w-80 h-80 rounded-full bg-gradient-to-tr from-rose-200/40 via-amber-100/30 to-transparent blur-3xl"></div>
  </div>

  <!-- Shared Universal Header -->
  <header class="fixed top-0 w-full z-50 pt-safe backdrop-blur-xl bg-white/75 border-b border-white/60 shadow-[0_2px_12px_rgba(0,0,0,0.03)]">
    <div class="h-14 px-4 flex items-center justify-between max-w-lg mx-auto">
      <div class="flex items-center gap-2.5">
        <div class="w-8 h-8 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center">
          <span class="material-symbols-outlined text-primary text-[19px]">account_balance</span>
        </div>
        <div class="flex flex-col">
          <span class="font-label-caps text-[10px] uppercase font-bold tracking-wider text-slate-400">TrueCost Autopilot</span>
          <span class="font-headline-md text-sm font-bold text-slate-800 leading-tight" id="header-folio-title">Part 01 · Capture Canvas</span>
        </div>
      </div>
      <div class="flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/80 border border-white/80 shadow-xs text-slate-700 font-label-caps text-[10px] uppercase tracking-wider backdrop-blur-sm">
        <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
        <span class="font-bold">AUD · IDR 10,360</span>
      </div>
    </div>
  </header>

  <!-- Main Content Container with 4 Tab Sections -->
  <main class="flex-1 flex flex-col relative w-full pt-16 pb-28 min-h-screen z-10">
    <!-- TAB 1: Capture -->
    <div id="section-capture" class="tab-section active">
      {main1}
    </div>

    <!-- TAB 2: Verdict -->
    <div id="section-verdict" class="tab-section">
      {main2}
    </div>

    <!-- TAB 3: Shield -->
    <div id="section-shield" class="tab-section">
      {main3}
    </div>

    <!-- TAB 4: Audit -->
    <div id="section-audit" class="tab-section">
      {main4}
    </div>
  </main>

  <!-- Universal Interactive (3 + 1) Dynamic Dock -->
  <nav class="fixed bottom-0 inset-x-0 z-50 pb-safe pointer-events-none flex justify-center">
    <div class="pointer-events-auto mx-4 mb-3 flex items-center gap-2 max-w-md w-full justify-center">
      <!-- Left Capsule: 3 Core Tabs -->
      <div class="dock-spring flex items-center rounded-full backdrop-blur-xl bg-white/85 border border-white/80 shadow-[0_8px_32px_rgba(0,0,0,0.08)] p-1.5" id="master-dock-left">
        <div class="flex items-center gap-1 dock-spring">
          <!-- Capture Tab -->
          <button id="dock-btn-capture" class="dock-tab flex items-center gap-1.5 py-1.5 px-3.5 rounded-full bg-slate-900 text-white shadow-sm dock-spring" onclick="switchTab('capture')">
            <span class="material-symbols-outlined text-[17px]">center_focus_strong</span>
            <span class="font-label-caps text-[10px] font-bold uppercase tracking-wider">Capture</span>
          </button>
          <!-- Verdict Tab -->
          <button id="dock-btn-verdict" class="dock-tab flex items-center gap-1.5 py-1.5 px-3 rounded-full text-slate-500 hover:text-slate-800 hover:bg-white/60 dock-spring" onclick="switchTab('verdict')">
            <span class="material-symbols-outlined text-[17px]">balance</span>
            <span class="font-label-caps text-[10px] font-medium uppercase tracking-wider">Verdict</span>
          </button>
          <!-- Shield Tab -->
          <button id="dock-btn-shield" class="dock-tab flex items-center gap-1.5 py-1.5 px-3 rounded-full text-slate-500 hover:text-slate-800 hover:bg-white/60 dock-spring" onclick="switchTab('shield')">
            <span class="material-symbols-outlined text-[17px]">verified_user</span>
            <span class="font-label-caps text-[10px] font-medium uppercase tracking-wider">Shield</span>
          </button>
        </div>
      </div>

      <!-- Right Capsule (+1 Module: Audit Vault) -->
      <div class="dock-spring flex items-center rounded-full backdrop-blur-xl bg-white/85 border border-white/80 shadow-[0_8px_32px_rgba(0,0,0,0.08)] p-1.5" id="master-dock-right">
        <button id="dock-btn-audit" class="flex items-center gap-1.5 py-1.5 px-3 rounded-full text-slate-600 hover:text-slate-900 hover:bg-white/60 dock-spring" onclick="switchTab('audit')" title="Sandbox Audit Trajectory">
          <div class="relative w-6 h-6 rounded-full bg-amber-100 text-amber-900 border border-amber-300 flex items-center justify-center">
            <span class="material-symbols-outlined text-[15px]">query_stats</span>
            <span class="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-emerald-500 ring-1 ring-white"></span>
          </div>
          <span class="font-label-caps text-[10px] font-bold uppercase tracking-wider">Audit</span>
        </button>
      </div>
    </div>
  </nav>

  <script>
    let activeTabName = 'capture';

    const titles = {{
      capture: 'Part 01 · Capture Canvas',
      verdict: 'Part 02 · Quant Verdict',
      shield: 'Part 03 · Scam Shield & HITL',
      audit: 'Part 04 · Sandbox Ledger & Audit'
    }};

    function switchTab(tab) {{
      activeTabName = tab;

      // Update header
      document.getElementById('header-folio-title').textContent = titles[tab] || 'TrueCost Autopilot';

      // Update section visibility
      ['capture', 'verdict', 'shield', 'audit'].forEach(t => {{
        const sec = document.getElementById('section-' + t);
        if (sec) {{
          if (t === tab) {{
            sec.classList.add('active');
          }} else {{
            sec.classList.remove('active');
          }}
        }}
      }});

      // Update Dock styling
      ['capture', 'verdict', 'shield'].forEach(t => {{
        const btn = document.getElementById('dock-btn-' + t);
        if (btn) {{
          if (t === tab) {{
            btn.className = 'dock-tab flex items-center gap-1.5 py-1.5 px-3.5 rounded-full bg-slate-900 text-white shadow-sm dock-spring';
          }} else {{
            btn.className = 'dock-tab flex items-center gap-1.5 py-1.5 px-3 rounded-full text-slate-500 hover:text-slate-800 hover:bg-white/60 dock-spring';
          }}
        }}
      }});

      const auditBtn = document.getElementById('dock-btn-audit');
      if (auditBtn) {{
        if (tab === 'audit') {{
          auditBtn.className = 'flex items-center gap-1.5 py-1.5 px-3.5 rounded-full bg-primary text-white shadow-sm dock-spring';
        }} else {{
          auditBtn.className = 'flex items-center gap-1.5 py-1.5 px-3 rounded-full text-slate-600 hover:text-slate-900 hover:bg-white/60 dock-spring';
        }}
      }}

      window.scrollTo({{ top: 0, behavior: 'smooth' }});

      // Notify native Android bridge if available
      if (window.AndroidBridge && window.AndroidBridge.onTabChanged) {{
        window.AndroidBridge.onTabChanged(tab);
      }}
    }}

    // Hook cross-screen interactions
    document.addEventListener('DOMContentLoaded', () => {{
      // Analyze button on Screen 1
      const analyzeBtn = document.getElementById('analyze-btn');
      if (analyzeBtn) {{
        analyzeBtn.addEventListener('click', () => {{
          switchTab('verdict');
        }});
      }}

      // ACTIVATE SHIELD button on Screen 2
      const activateShieldBtns = document.querySelectorAll('button');
      activateShieldBtns.forEach(b => {{
        if (b.textContent.trim().includes('ACTIVATE SHIELD')) {{
          b.addEventListener('click', () => {{
            switchTab('shield');
          }});
        }}
      }});

      // HITL Confirm on Screen 3
      const hitlConfirm = document.getElementById('btn-hitl-confirm');
      if (hitlConfirm) {{
        hitlConfirm.addEventListener('click', () => {{
          setTimeout(() => {{
            switchTab('audit');
          }}, 1300);
        }});
      }}
    }});

    // Preset selection helper
    function selectPreset(type) {{
      const input = document.getElementById('url-input');
      if (type === 'bnpl') {{
        if (input) input.value = "https://store.apple.com/au/macbook-air-m3-afterpay-split";
        setTimeout(() => switchTab('verdict'), 300);
      }} else if (type === 'deal') {{
        if (input) input.value = "https://lenovo.com/au/thinkpad-x1-carbon-trs-export";
        setTimeout(() => switchTab('verdict'), 300);
      }} else if (type === 'scam') {{
        if (input) input.value = "https://discount-gpu-outlet.biz/rog-strix-4080-wire-transfer";
        setTimeout(() => switchTab('shield'), 300);
      }}
    }}
  </script>
</body>
</html>
"""
    with open("stitch_output/index.html", "w", encoding="utf-8") as f:
        f.write(unified_html)
    print(f"Generated stitch_output/index.html ({len(unified_html)} bytes)")

if __name__ == "__main__":
    create_unified_html()
