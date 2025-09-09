"""
run_daily.py
------------
Runs the daily scraping job:
1. Scrape updates from multiple sources (RSS feeds)
2. Deduplicate (avoid inserting same article twice)
3. Enrich text with AI (summarizer)
4. Insert into database
5. Send Slack alert (optional)
"""

from scrapers.news_scraper import scrape_updates
from ai_enrichment.summarizer import enrich_update
from database.models import SessionLocal, Opportunity
from alerts.slack_alert import send_slack_alert
from datetime import datetime

db = SessionLocal()

print("🚀 Starting run_daily.py...")

# Step 1: Get updates from feeds
updates = scrape_updates()
print(f"🔎 Scraper returned {len(updates)} updates")

# Step 2: Fallback if nothing found
if not updates:
    existing = db.query(Opportunity).count()
    if existing == 0:  # Only insert dummy data if DB is empty
        print("⚠️ No updates found. Inserting dummy test data...")
        updates = [
            {
                "title": "PFAS Regulation Update",
                "description": "New PFAS regulation introduced in the US.",
                "pub_date": datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT"),
                "link": "https://www.epa.gov/pfas",
                "source": "Dummy"
            },
            {
                "title": "Water Treatment Innovation",
                "description": "New water treatment technology shows promise.",
                "pub_date": datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT"),
                "link": "https://www.epa.gov/water",
                "source": "Dummy"
            }
        ]
    else:
        print("⚠️ No updates found, skipping insert to avoid duplicates.")
        updates = []

# Step 3: Insert updates into DB
for update in updates:
    try:
        # Convert pub_date safely
        try:
            pub_date = datetime.strptime(update["pub_date"], "%a, %d %b %Y %H:%M:%S %Z")
        except Exception:
            pub_date = datetime.now()

        # Deduplication check (by link)
        exists = db.query(Opportunity).filter_by(link=update["link"]).first()
        if exists:
            print(f"⚠️ Skipping duplicate: {update['title']}")
            continue

        # Process & insert
        print(f"📰 Processing: {update['title']}")
        summary = enrich_update(update["description"])

        opp = Opportunity(
            title=update["title"],
            summary=summary,
            source=update.get("source", "News Feed"),
            date=pub_date,
            link=update["link"]
        )
        db.add(opp)
        send_slack_alert(f"🚨 New Update: {update['title']}")
        print(f"✅ Inserted: {update['title']}")

    except Exception as e:
        print(f"❌ Failed to insert {update.get('title', 'UNKNOWN')}: {e}")

db.commit()
print("💾 All changes committed to DB.")

db.close()
print("🏁 run_daily.py finished.")
