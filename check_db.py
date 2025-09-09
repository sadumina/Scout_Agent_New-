import sqlite3

# Connect to your SQLite database file
conn = sqlite3.connect("market_scout.db")
cur = conn.cursor()

# Check if opportunities table exists
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='opportunities';")
table_exists = cur.fetchone()

if not table_exists:
    print("⚠️ Table 'opportunities' does not exist in market_scout.db")
else:
    # Fetch some rows
    cur.execute("SELECT id, title, source, date FROM opportunities LIMIT 5;")
    rows = cur.fetchall()

    if not rows:
        print("⚠️ No opportunities found in the DB")
    else:
        print("✅ Found opportunities:")
        for row in rows:
            print(row)

conn.close()
