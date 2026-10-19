import asyncio
import json
import os
import subprocess
import time
import urllib.request
import websockets

ADB_PATH = os.path.expandvars(r"$LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe")

def run_adb(cmd):
    full_cmd = f'"{ADB_PATH}" {cmd}'
    res = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    return res.stdout.strip()

def capture_screen(device_path, local_path):
    run_adb(f"shell screencap -p {device_path}")
    run_adb(f"pull {device_path} {local_path}")
    print(f"Captured {local_path} ({os.path.getsize(local_path):,} bytes)")

async def main():
    # 1. Forward devtools port
    run_adb("forward tcp:9222 localabstract:webview_devtools_remote_12506")
    
    # 2. Get WebSocket debugger URL
    resp = urllib.request.urlopen("http://localhost:9222/json")
    pages = json.loads(resp.read().decode())
    target_page = None
    for p in pages:
        if "index.html" in p.get("url", ""):
            target_page = p
            break
    if not target_page:
        target_page = pages[0]
        
    ws_url = target_page["webSocketDebuggerUrl"]
    print("Connecting to DevTools at:", ws_url)
    
    async with websockets.connect(ws_url) as ws:
        msg_id = 0
        
        async def eval_js(expr):
            nonlocal msg_id
            msg_id += 1
            payload = {
                "id": msg_id,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": expr,
                    "awaitPromise": True
                }
            }
            await ws.send(json.dumps(payload))
            while True:
                raw = await ws.recv()
                data = json.loads(raw)
                if data.get("id") == msg_id:
                    return data.get("result", {})
                    
        # --- INITIALIZATION ---
        print("Initializing app with ThinkPad T14s deal...")
        await eval_js("finishOnboarding(); setFreshUserMode(false); await selectPreset('deal');")
        await asyncio.sleep(2.5)

        # --- SCREEN 1: Capture / Home Canvas ---
        print("\n--- Generating Screen 1 (Capture / Home Canvas) ---")
        await eval_js("closeExpansionSheet(); switchTab('capture');")
        await asyncio.sleep(2.5)
        capture_screen("/sdcard/live_screen1.png", "docs/diagrams/phone1.png")

        # --- SCREEN SHEET: Upward Spring Expansion Modal Sheet ---
        print("\n--- Generating Screen Sheet (Upward Spring Expansion) ---")
        await eval_js("openExpansionSheet();")
        await asyncio.sleep(2.0)
        capture_screen("/sdcard/live_phonesheet.png", "docs/diagrams/phonesheet.png")

        # --- SCREEN 2: Deterministic Deal Analysis (Verdict) ---
        print("\n--- Generating Screen 2 (Deal Analysis / Verdict) ---")
        await eval_js("closeExpansionSheet(); switchTab('verdict'); switchVerdictSubtab('landed');")
        await asyncio.sleep(2.5)
        capture_screen("/sdcard/live_screen2.png", "docs/diagrams/phone2.png")

        # --- SCREEN 3: Scam Shield & Cognitive Friction Gate ---
        print("\n--- Generating Screen 3 (Scam Shield) ---")
        await eval_js("await selectPreset('scam'); switchTab('shield');")
        await asyncio.sleep(2.5)
        capture_screen("/sdcard/live_screen3.png", "docs/diagrams/phone3.png")

        # --- SCREEN 4: Student Safety Log & Bank Ledger ---
        print("\n--- Generating Screen 4 (Student Safety Log & Ledger with Settled Escrow) ---")
        await eval_js("await selectPreset('deal'); await doRealMoneyFlow('reserve_and_settle'); switchTab('audit');")
        await asyncio.sleep(2.5)
        capture_screen("/sdcard/live_screen4.png", "docs/diagrams/phone4.png")

    print("\nALL REAL SCREENSHOTS CAPTURED AND SYNCHRONIZED SUCCESSFULLY FROM CONNECTED DEVICE!")

if __name__ == "__main__":
    asyncio.run(main())
