import shutil
import os

os.makedirs("android_assets", exist_ok=True)

# Copy html files
shutil.copy("stitch_output/index.html", "android_assets/index.html")
shutil.copy("stitch_output/f362326752ab4e7b8a0797da9f50fc40.html", "android_assets/screen1_capture.html")
shutil.copy("stitch_output/c967f13527324ad591b2b39d38db0fd1.html", "android_assets/screen2_verdict.html")
shutil.copy("stitch_output/9ece5206870b40fabc05bca5533a4fe2.html", "android_assets/screen3_shield.html")
shutil.copy("stitch_output/fdb14843450b47bb9f1317cd20b6f554.html", "android_assets/screen4_audit.html")

# Copy png screenshots
shutil.copy("stitch_output/f362326752ab4e7b8a0797da9f50fc40.png", "android_assets/screen1.png")
shutil.copy("stitch_output/c967f13527324ad591b2b39d38db0fd1.png", "android_assets/screen2.png")
shutil.copy("stitch_output/9ece5206870b40fabc05bca5533a4fe2.png", "android_assets/screen3.png")
shutil.copy("stitch_output/fdb14843450b47bb9f1317cd20b6f554.png", "android_assets/screen4.png")

print("android_assets populated:")
for f in os.listdir("android_assets"):
    print(f"  {f} ({os.path.getsize(os.path.join('android_assets', f))} bytes)")
