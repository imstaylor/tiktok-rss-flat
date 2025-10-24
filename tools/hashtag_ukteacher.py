# Minimal hashtag->RSS builder that fits a GitHub Pages layout
# Saves to rss/hashtag-ukteacher.xml

import os, html, re, json, pathlib
import datetime as dt
import requests

BASE = "https://www.tiktok.com"
TAG  = "ukteacher"
OUT  = pathlib.Path("rss/hashtag-ukteacher.xml")
OUT.parent.mkdir(parents=True, exist_ok=True)

session = requests.Session()
ms = os.environ.get("MS_TOKEN", "")
if ms:
    session.cookies.set("msToken", ms, domain=".tiktok.com")

url = f"{BASE}/tag/{TAG}"
headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": BASE + "/",
    "Accept-Language": "en-GB,en;q=0.9",
}
r = session.get(url, headers=headers, timeout=30)
r.raise_for_status()
html_text = r.text

m = re.search(r'<script id="SIGI_STATE".*?>(.*?)</script>', html_text, re.S)
data = json.loads(m.group(1)) if m else {}

aweme_map = data.get("ItemModule", {})
tag_videos = []
for _, obj in aweme_map.items():
    desc = (obj.get("desc") or "").lower()
    if "#ukteacher" in desc.replace(" ", "") or "ukteacher" in desc:
        tag_videos.append(obj)

now_rfc = dt.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

def esc(x): return html.escape(str(x or ""))

rss_items = []
for v in sorted(tag_videos, key=lambda x: x.get("createTime", "0"), reverse=True)[:30]:
    title = v.get("desc") or f"Video by {v.get('author', '')}"
    link  = f"{BASE}/@{v.get('author', '')}/video/{v.get('id', '')}"
    pub   = dt.datetime.utcfromtimestamp(int(v.get("createTime", "0"))).strftime("%a, %d %b %Y %H:%M:%S +0000")
    thumb = (v.get("video") or {}).get("cover")
    author= v.get("author", "")

    rss_items.append(f"""
    <item>
      <title>{esc(title)}</title>
      <link>{esc(link)}</link>
      <guid isPermaLink="true">{esc(link)}</guid>
      <pubDate>{pub}</pubDate>
      <author>{esc(author)}</author>
{('<enclosure url="' + esc(thumb) + '" type="image/jpeg" />') if thumb else ""}
      <description>{esc(title)}</description>
    </item>
    """)

rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>TikTok hashtag: #ukteacher</title>
  <link>{esc(url)}</link>
  <description>Unofficial RSS for TikTok hashtag #ukteacher</description>
  <lastBuildDate>{now_rfc}</lastBuildDate>
  {''.join(rss_items)}
</channel>
</rss>
"""

OUT.write_text(rss, encoding="utf-8")
print(f"Wrote {OUT} with {len(rss_items)} items.")
