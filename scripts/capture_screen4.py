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
                    
        print("Executing reserve_and_settle and navigating directly to My Vault & Accounts (audit)...")
        await eval_js("closeExpansionSheet();")
        await asyncio.sleep(0.5)
        await eval_js("if (typeof doRealMoneyFlow === 'function') { doRealMoneyFlow('reserve_and_settle'); }")
        await asyncio.sleep(1.0)
        await eval_js("switchTab('audit');")
        await asyncio.sleep(2.0)
        
        # Verify active tab
        res = await eval_js("activeTabName;")
        print("Active tab in app:", res.get("value"))
        
        capture_screen("/sdcard/live_screen4.png", "docs/diagrams/phone4.png")
        print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
