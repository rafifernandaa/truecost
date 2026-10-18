import json
import os
import subprocess

def inspect_screens():
    screen_ids = [
        "9ece5206870b40fabc05bca5533a4fe2",
        "fdb14843450b47bb9f1317cd20b6f554",
        "c967f13527324ad591b2b39d38db0fd1",
        "f362326752ab4e7b8a0797da9f50fc40"
    ]

    for sid in screen_ids:
        path = f"stitch_output/{sid}.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        content = data.get("result", {}).get("content", [])
        if content and "text" in content[0]:
            screen_obj = json.loads(content[0]["text"])
            title = screen_obj.get("title", "Untitled")
            print(f"\n================ Screen: {sid} ================")
            print(f"Title: {title}")
            print(f"Keys: {list(screen_obj.keys())}")
            
            # Check screenshot
            screenshot = screen_obj.get("screenshot", {})
            screenshot_url = screenshot.get("downloadUrl", "")
            print(f"Screenshot URL: {screenshot_url[:100]}...")
            
            html_code = screen_obj.get("htmlCode")
            print(f"HTML code type: {type(html_code)}")
            if isinstance(html_code, dict):
                print(f"HTML code keys: {list(html_code.keys())}")
                print(f"HTML code dict content: {html_code}")
                # check if there is downloadUrl
                if "downloadUrl" in html_code:
                    html_url = html_code["downloadUrl"]
                    html_path = f"stitch_output/{sid}.html"
                    print(f"Downloading HTML from {html_url[:60]}... via curl -L")
                    cmd = ["curl.exe", "-L", "-s", "-o", html_path, html_url]
                    subprocess.run(cmd, check=True)
                    print(f"Saved {html_path} ({os.path.getsize(html_path)} bytes)")
            elif isinstance(html_code, str):
                with open(f"stitch_output/{sid}.html", "w", encoding="utf-8") as hf:
                    hf.write(html_code)
                print(f"Saved stitch_output/{sid}.html")


            # Download screenshot using curl -L as requested by user
            if screenshot_url:
                img_path = f"stitch_output/{sid}.png"
                print(f"Downloading image to {img_path} via curl -L ...")
                cmd = ["curl.exe", "-L", "-s", "-o", img_path, screenshot_url]
                subprocess.run(cmd, check=True)
                print(f"Downloaded {img_path} (size: {os.path.getsize(img_path)} bytes)")

if __name__ == "__main__":
    inspect_screens()
