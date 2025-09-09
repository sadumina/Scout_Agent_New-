import sqlite3

conn = sqlite3.connect("market_scout.db")
cur = conn.cursor()

cur.execute("SELECT product, COUNT(*) FROM opportunities GROUP BY product;")
rows = cur.fetchall()
print(rows)

conn.close()
