import requests
import feedparser

NEWS_FEED_URL = "https://grist.org/feed/"   # 👈 switch to a real feed

def scrape_updates():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(NEWS_FEED_URL, headers=headers, timeout=10)
        resp.raise_for_status()
        feed = feedparser.parse(resp.text)

        updates = []
        for entry in feed.entries:
            updates.append({
                "title": entry.title,
                "description": getattr(entry, "summary", ""),
                "pub_date": getattr(entry, "published", ""),
                "link": entry.link
            })
        return updates
    except Exception as e:
        print(f"❌ Failed to scrape feed: {e}")
        return []
