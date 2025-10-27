# db.py
import aiosqlite

DB_NAME = "news_cache.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS news_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product TEXT,
                title TEXT UNIQUE,
                summary TEXT,
                source TEXT,
                date TEXT,
                link TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def insert_article(product, article):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT OR IGNORE INTO news_cache (product, title, summary, source, date, link)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (product, article["title"], article["summary"], article["source"], article["date"], article["link"]))
        await db.commit()

async def get_cached_articles(product, limit=10):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            SELECT title, summary, source, date, link FROM news_cache
            WHERE product = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (product, limit))
        rows = await cursor.fetchall()
    return [
        {"title": r[0], "summary": r[1], "source": r[2], "date": r[3], "link": r[4]}
        for r in rows
    ]
