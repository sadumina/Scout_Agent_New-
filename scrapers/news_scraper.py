import requests
import feedparser
from bs4 import BeautifulSoup

FEED_URLS = {
    "Google News (PFAS)": "https://news.google.com/rss/search?q=PFAS",
    # "EcoWatch": "https://www.ecowatch.com/rss/feed",
    # "Yale E360": "https://e360.yale.edu/feed.xml",
    # "EPA Newsroom": "https://www.epa.gov/newsreleases/search/rss.xml",
}

def clean_html(raw_html: str) -> str:
    """Remove HTML tags and return plain text."""
    if not raw_html:
        return ""
    return BeautifulSoup(raw_html, "html.parser").get_text(" ", strip=True)

def scrape_updates():
    updates = []
    headers = {"User-Agent": "Mozilla/5.0"}

    for label, url in FEED_URLS.items():
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)

            for entry in feed.entries[:10]:
                updates.append({
                    "title": entry.title,
                    "description": clean_html(getattr(entry, "summary", "")),
                    "pub_date": getattr(entry, "published", ""),
                    "link": entry.link,
                    "source": label  # ✅ use friendly label, not feed URL
                })

            print(f"✅ Parsed {len(feed.entries)} entries from {label}")

        except Exception as e:
            print(f"⚠️ Failed to fetch {label}: {e}")

    return updates
