import requests
import feedparser
from bs4 import BeautifulSoup

# ✅ RSS Feed URLs (Google News searches + special categories)
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
    "EDLC": "https://news.google.com/rss/search?q=supercapacitor+EDLC",
    "Silicon Anodes": "https://news.google.com/rss/search?q=silicon+anodes+battery",
    "Lithium Iron Batteries": "https://news.google.com/rss/search?q=lithium+iron+phosphate+battery",
    "Carbon Block Filters": "https://news.google.com/rss/search?q=activated+carbon+block+filters",

    # ✅ New Activated Carbon categories
    "Activated Carbon for Gold Recovery": "https://news.google.com/rss/search?q=activated+carbon+gold+recovery",
    "Activated Carbon for EDLC": "https://news.google.com/rss/search?q=activated+carbon+EDLC",
    "Activated Carbon for Silicon Anodes": "https://news.google.com/rss/search?q=activated+carbon+silicon+anodes",

    # ✅ Haycarb news via Google News
    "Haycarb Updates": "https://news.google.com/rss/search?q=Haycarb"
}


def clean_html(raw_html: str) -> str:
    """Remove HTML tags and return plain text."""
    if not raw_html:
        return ""
    return BeautifulSoup(raw_html, "html.parser").get_text(" ", strip=True)


# ✅ Scraper for Jacobi website (still homepage-based)
def scrape_jacobi():
    url = "https://www.jacobi.net/"
    try:
        res = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, "html.parser")
        items = []
        for a in soup.find_all("a", href=True)[:5]:
            text = a.get_text(strip=True)
            if text:
                items.append({
                    "title": text,
                    "description": "Update from Jacobi website",
                    "pub_date": "",
                    "link": a["href"] if a["href"].startswith("http") else url + a["href"],
                    "source": "Jacobi",
                    "product": "Jacobi Updates",
                })
        return items
    except Exception as e:
        return [{
            "title": f"Error fetching Jacobi: {e}",
            "description": "",
            "pub_date": "",
            "link": url,
            "source": "Jacobi",
            "product": "Jacobi Updates",
        }]


def scrape_updates():
    """Scrape Google News feeds + Jacobi homepage."""
    updates = []
    headers = {"User-Agent": "Mozilla/5.0"}

    # ✅ Loop over feeds
    for product, url in FEED_URLS.items():
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
                    "source": product,
                    "product": product,
                })

            print(f"✅ Parsed {len(feed.entries)} entries for {product}")

        except Exception as e:
            print(f"⚠️ Failed to fetch {product}: {e}")

    # ✅ Add Jacobi homepage scraping
    updates.extend(scrape_jacobi())

    return updates
