from scrapers.news_scraper import scrape_updates
from ai_enrichment.summarizer import enrich_update
from database.models import SessionLocal, Opportunity
from alerts.slack_alert import send_slack_alert
from datetime import datetime

db = SessionLocal()

print("🚀 Starting run_daily.py...")

# Step 1: Scrape updates
updates = scrape_updates()
print(f"🔎 Scraper returned {len(updates)} updates")

if not updates:
    print("⚠️ No updates found. Skipping.")
    db.close()
    exit()

# Step 2: Insert into DB
for update in updates:
    try:
        try:
            pub_date = datetime.strptime(update["pub_date"], "%a, %d %b %Y %H:%M:%S %Z")
        except Exception:
            pub_date = datetime.now()

        # Deduplication check
        exists = db.query(Opportunity).filter_by(link=update["link"]).first()
        if exists:
            print(f"⚠️ Skipping duplicate: {update['title']}")
            continue

        print(f"📰 Processing: {update['title']}")
        summary = enrich_update(update["description"])

        opp = Opportunity(
            title=update["title"],
            summary=summary,
            source=update.get("source", "News Feed"),
            date=pub_date,
            link=update["link"],
            product=update.get("product", "PFAS")  # ✅ dynamic product
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
