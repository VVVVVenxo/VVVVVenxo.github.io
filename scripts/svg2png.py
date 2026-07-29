"""SVG -> PNG（headless Chrome/Chromium）。跨平台：本地 Windows 与 CI Linux 通用。
用法: python svg2png.py [目录]   默认转 source/img/covers/gen
只转比对应 PNG 新的 SVG（增量）。"""
import glob, os, urllib.parse, subprocess, sys, shutil

def find_chrome():
    env = os.environ.get("CHROME_BIN")
    if env and os.path.exists(env):
        return env
    for name in ("google-chrome", "google-chrome-stable", "chromium",
                 "chromium-browser", "chrome"):
        p = shutil.which(name)
        if p:
            return p
    for p in (r"C:/Program Files/Google/Chrome/Application/chrome.exe",
              r"C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
              r"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"):
        if os.path.exists(p):
            return p
    raise SystemExit("no chrome/chromium found; set CHROME_BIN")

def main():
    chrome = find_chrome()
    d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "source", "img", "covers", "gen")
    svgs = glob.glob(os.path.join(d, "*.svg"))
    n = 0
    for svg in svgs:
        png = svg[:-4] + ".png"
        if os.path.exists(png) and os.path.getmtime(png) >= os.path.getmtime(svg):
            continue  # 增量：PNG 已是最新
        url = "file:///" + urllib.parse.quote(svg.replace("\\", "/"))
        subprocess.run([chrome, "--headless", "--disable-gpu", "--no-sandbox",
                        "--screenshot=" + png, "--window-size=1200,630",
                        "--force-device-scale-factor=1", url],
                       capture_output=True)
        n += 1
    print(f"svg2png: converted {n}, total svg {len(svgs)}, chrome={chrome}")

if __name__ == "__main__":
    main()
