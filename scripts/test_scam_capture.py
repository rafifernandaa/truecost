import asyncio
import json
import os
import subprocess
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
    run_adb("forward tcp:9222 localabstract:webview_devtools_remote_12506")
    resp = urllib.request.urlopen("http://localhost:9222/json")
    pages = json.loads(resp.read().decode())
    target_page = [p for p in pages if "index.html" in p.get("url", "")][0]
    ws_url = target_page["webSocketDebuggerUrl"]
    print("Connecting to:", ws_url)
    
    async with websockets.connect(ws_url) as ws:
        msg_id = 0
        async def eval_js(expr):
            nonlocal msg_id
            msg_id += 1
            payload = {
                "id": msg_id,
                "method": "Runtime.evaluate",
                "params": {"expression": expr, "awaitPromise": True}
            }
            await ws.send(json.dumps(payload))
            while True:
                raw = await ws.recv()
                data = json.loads(raw)
                if data.get("id") == msg_id:
                    return data.get("result", {})

        print("Testing selectPreset('scam')...")
        res1 = await eval_js("selectPreset('scam')")
        print("selectPreset result:", res1)
        await asyncio.sleep(2.0)
        res2 = await eval_js("switchTab('shield');")
        print("switchTab('shield') result:", res2)
        await asyncio.sleep(1.5)
        res3 = await eval_js("activeTabName;")
        print("Active tab name:", res3)
        capture_screen("/sdcard/live_screen3.png", "docs/diagrams/phone3.png")

if __name__ == "__main__":
    asyncio.run(main())
