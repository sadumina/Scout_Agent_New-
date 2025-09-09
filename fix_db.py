import sqlite3

DB_PATH = "market_scout.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Check if 'product' column exists
cur.execute("PRAGMA table_info(opportunities);")
columns = [col[1] for col in cur.fetchall()]

if "product" not in columns:
    print("➡️ Adding missing 'product' column...")
    cur.execute("ALTER TABLE opportunities ADD COLUMN product TEXT;")
    conn.commit()
    print("✅ Column added successfully")
else:
    print("✔️ 'product' column already exists")

conn.close()
