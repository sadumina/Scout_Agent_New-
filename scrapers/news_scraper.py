import requests
import feedparser
from bs4 import BeautifulSoup

FEED_URLS = {
   "PFAS": "https://news.google.com/rss/search?q=PFAS",
    "Soil Remediation": "https://news.google.com/rss/search?q=soil+remediation",
    "Mining": "https://news.google.com/rss/search?q=mining+gold",
    "Gold Recovery": "https://news.google.com/rss/search?q=gold+recovery",
    "Drinking Water": "https://news.google.com/rss/search?q=drinking+water+treatment",
    "Wastewater Treatment": "https://news.google.com/rss/search?q=wastewater+treatment",
    "Air & Gas Purification": "https://news.google.com/rss/search?q=air+gas+purification",
    "Mercury Removal": "https://news.google.com/rss/search?q=mercury+removal",
    "Food & Beverage": "https://news.google.com/rss/search?q=food+beverage+filtration",
    "Energy Storage": "https://news.google.com/rss/search?q=energy+storage+carbon",
    "Catalyst Support": "https://news.google.com/rss/search?q=catalyst+support+carbon",
    "Automotive Filters": "https://news.google.com/rss/search?q=automotive+carbon+filter",
    "Medical & Pharma": "https://news.google.com/rss/search?q=medical+pharma+carbon",
    "Nuclear Applications": "https://news.google.com/rss/search?q=nuclear+carbon+filter",
}

def clean_html(raw_html: str) -> str:
    """Remove HTML tags and return plain text."""
    if not raw_html:
        return ""
    return BeautifulSoup(raw_html, "html.parser").get_text(" ", strip=True)

def scrape_updates():
    updates = []
    headers = {"User-Agent": "Mozilla/5.0"}

    for product, url in FEED_URLS.items():
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)

            for entry in feed.entries[:10]:
                updates.append({
                    "title": entry.title,
                    "description": clean_html(getattr(entry, "summary", "")),  # ✅ now works
                    "pub_date": getattr(entry, "published", ""),
                    "link": entry.link,
                    "source": product,
                    "product": product,  # ✅ critical
                })

            print(f"✅ Parsed {len(feed.entries)} entries for {product}")

        except Exception as e:
            print(f"⚠️ Failed to fetch {product}: {e}")

    return updates
