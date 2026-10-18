import urllib.request
import json
import os

API_KEY = os.environ.get("STITCH_API_KEY", "")
URL = "https://stitch.googleapis.com/mcp"

def call_mcp(method, params=None):
    if params is None:
        params = {}
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params
    }
    req = urllib.request.Request(
        URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": API_KEY
        }
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def call_tool(tool_name, arguments):
    return call_mcp("tools/call", {"name": tool_name, "arguments": arguments})

def main():
    project_id = "5894247679312562472"
    print(f"Fetching project projects/{project_id}...")
    proj_resp = call_tool("get_project", {"name": f"projects/{project_id}"})
    print("Project response:")
    print(json.dumps(proj_resp, indent=2)[:500])

    screen_ids = [
        "9ece5206870b40fabc05bca5533a4fe2",
        "fdb14843450b47bb9f1317cd20b6f554",
        "c967f13527324ad591b2b39d38db0fd1",
        "f362326752ab4e7b8a0797da9f50fc40"
    ]

    for sid in screen_ids:
        print(f"\n--- Fetching screen {sid} ---")
        screen_resp = call_tool("get_screen", {"name": f"projects/{project_id}/screens/{sid}"})
        # Save raw response
        os.makedirs("stitch_output", exist_ok=True)
        with open(f"stitch_output/{sid}.json", "w", encoding="utf-8") as f:
            json.dump(screen_resp, f, indent=2)
        print(f"Saved stitch_output/{sid}.json")




if __name__ == "__main__":
    main()
