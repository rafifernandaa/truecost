#!/usr/bin/env python3
"""
TrueCost Autopilot - Interactive Browser Preview Runner
Serves the TrueCost interactive prototype on http://localhost:8080 with the phone mockup chassis.
"""
import os
import sys
import http.server
import socketserver
import webbrowser
from pathlib import Path

# Fix Windows console UTF-8 encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PORT = 8080
ROOT_DIR = Path(__file__).resolve().parent / "android_app" / "app" / "src" / "main" / "assets" / "www"

class TrueCostPreviewHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT_DIR), **kwargs)

    def do_GET(self):
        # Default root requests go to the interactive preview studio
        if self.path in ("/", ""):
            self.send_response(302)
            self.send_header("Location", "/preview.html")
            self.end_headers()
            return
        super().do_GET()

    def log_message(self, format, *args):
        # Keep terminal output clean
        pass

def run_server(port=PORT):
    socketserver.TCPServer.allow_reuse_address = True
    
    server_address = ("", port)
    try:
        httpd = socketserver.TCPServer(server_address, TrueCostPreviewHandler)
    except OSError:
        port = 8081
        httpd = socketserver.TCPServer(("", port), TrueCostPreviewHandler)

    url = f"http://localhost:{port}/preview.html"
    print("=" * 64)
    print("  [TrueCost Autopilot] Live Browser Preview Studio")
    print(f"  Asset Directory: {ROOT_DIR}")
    print(f"  Preview Studio:  {url}")
    print(f"  Direct Web App:  http://localhost:{port}/index.html")
    print("=" * 64)
    print("  Available Test Scenarios:")
    print("  [1] BNPL Lie Detector (MacBook Air - 18.4% APR)")
    print("  [2] AU Tax TRS Export (ThinkPad X1 - +10% Back)")
    print("  [3] Scam Risk Interception (ROG Strix - Blocked)")
    print("=" * 64)
    print("  Server is active. Press Ctrl+C to stop.\n")

    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"  Note: Open {url} in your browser ({e})")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopping preview server...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
