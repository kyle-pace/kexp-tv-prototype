# Fetch KEXP's public YouTube feed (latest 15 uploads) as JSON.
# Used by server.py locally, and by the GitHub Action that refreshes videos.json on the live site.
# Usage: python3 videos.py [out.json]
import json, re, html, subprocess, sys, time, urllib.request

FEED = "https://www.youtube.com/feeds/videos.xml?channel_id=UC3I2GFN_F8WudD_2jUZbojA"  # KEXP

def _get(url):
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return r.read().decode("utf-8")
    except Exception:
        # macOS's bundled Python sometimes lacks certificates; curl always has them
        return subprocess.run(["curl", "-s", "-m", "15", url], capture_output=True, text=True).stdout

def fetch(tries=4):
    # YouTube's feed sometimes answers with an error page instead of the video list.
    # Try a few times, waiting a little longer each time, before giving up.
    for attempt in range(tries):
        vids = _parse(_get(FEED))
        if vids:
            return vids
        if attempt < tries - 1:
            time.sleep(10 * (attempt + 1))
    return []

def _parse(x):
    out = []
    for e in re.findall(r"<entry>(.*?)</entry>", x, re.S):
        def g(p):
            m = re.search(p, e, re.S)
            return m.group(1) if m else ""
        out.append({
            "id": g(r"<yt:videoId>(.*?)</yt:videoId>"),
            "title": html.unescape(g(r"<title>(.*?)</title>")),
            "published": g(r"<published>(.*?)</published>"),
            "views": int(g(r'views="(\d+)"') or 0),
        })
    return [v for v in out if v["id"]]

if __name__ == "__main__":
    vids = fetch()
    if not vids:
        # Not worth a failed run: the site keeps the last good list and the next run tries again.
        print("::warning::YouTube feed returned no videos after retries; keeping the old videos.json.")
        sys.exit(0)
    data = json.dumps(vids, ensure_ascii=False, indent=1)
    if len(sys.argv) > 1:
        open(sys.argv[1], "w", encoding="utf-8").write(data + "\n")
        print(f"Wrote {len(vids)} videos to {sys.argv[1]}")
    else:
        print(data)
