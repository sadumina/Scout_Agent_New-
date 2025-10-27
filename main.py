import os
import json
import asyncio
import httpx
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from openai import OpenAI
from db import init_db, insert_article, get_cached_articles

# ======================================
# 🔧 CONFIG
# ======================================
load_dotenv()
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")
CURRENTS_API_KEY = os.getenv("CURRENTS_API_KEY", "")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")

app = FastAPI(title="HAYCARB Market Scout API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ✅ Change to ["http://localhost:5173"] in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

connections: List[WebSocket] = []
client = OpenAI(api_key=OPENAI_KEY)

# ======================================
# 🧠 AI SUMMARIZATION
# ======================================
async def ai_summarize(text: str) -> str:
    if not text:
        return "No description available."
    try:
        prompt = f"Summarize this business article in one short insight (max 25 words):\n\n{text}"
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        summary = response.choices[0].message.content.strip()
        return re.sub(r"\s+", " ", summary)
    except Exception as e:
        print("⚠️ AI summarization error:", e)
        return (text[:150] + "...") if len(text) > 150 else text


# ======================================
# 🌍 FETCH NEWS — CurrentsAPI + GNews Fallback
# ======================================
async def fetch_currents(product: str, limit: int = 8):
    """Fetch global news from CurrentsAPI."""
    if not CURRENTS_API_KEY:
        print("⚠️ No CurrentsAPI key found — skipping.")
        return []

    url = f"https://api.currentsapi.services/v1/search?apiKey={CURRENTS_API_KEY}&language=en&keywords={product}"
    async with httpx.AsyncClient() as http:
        try:
            res = await http.get(url, timeout=15)
            if res.status_code == 429:
                print(f"❌ CurrentsAPI rate limit hit for {product}")
                return []
            if res.status_code != 200:
                print(f"❌ CurrentsAPI error: {res.status_code}")
                return []
            articles = res.json().get("news", [])
        except Exception as e:
            print("❌ CurrentsAPI fetch error:", e)
            return []

    return [
        {
            "title": a.get("title"),
            "source": a.get("author", "Unknown"),
            "date": a.get("published"),
            "summary": a.get("description") or "No description",
            "link": a.get("url"),
        }
        for a in articles[:limit]
        if a.get("title")
    ]


async def fetch_gnews(product: str, limit: int = 8):
    """Fallback to GNews if CurrentsAPI fails."""
    if not GNEWS_API_KEY:
        print("⚠️ No GNews key found — returning mock data.")
        return [
            {
                "title": f"{product} Market Expansion in Asia",
                "source": "Market Watch",
                "date": "2025-10-27T10:00:00Z",
                "summary": f"Strong demand for {product} applications in Asia-Pacific.",
                "link": "https://example.com/news1",
            },
            {
                "title": f"{product} Policy Updates Released",
                "source": "Environmental Insights",
                "date": "2025-10-25T09:00:00Z",
                "summary": f"Recent policy changes impact {product} standards.",
                "link": "https://example.com/news2",
            },
        ]

    url = (
        f"https://gnews.io/api/v4/search?q={product}&lang=en&country=us"
        f"&sortby=publishedAt&max={limit}&token={GNEWS_API_KEY}"
    )
    async with httpx.AsyncClient() as http:
        try:
            res = await http.get(url, timeout=15)
            if res.status_code != 200:
                print(f"❌ GNews error: {res.status_code}")
                return []
            data = res.json().get("articles", [])
        except Exception as e:
            print("❌ GNews fetch error:", e)
            return []

    return [
        {
            "title": a.get("title"),
            "source": (a.get("source") or {}).get("name", "Unknown"),
            "date": a.get("publishedAt"),
            "summary": a.get("description") or "No description",
            "link": a.get("url"),
        }
        for a in data
        if a.get("title")
    ]


async def fetch_news(product: str, limit: int = 8):
    """Try CurrentsAPI first, then fallback to GNews."""
    news = await fetch_currents(product, limit)
    if not news:
        print(f"🔁 Falling back to GNews for {product}")
        news = await fetch_gnews(product, limit)
    return news


# ======================================
# 📦 OPPORTUNITIES ENDPOINT
# ======================================
@app.get("/opportunities")
async def get_opportunities(product: str, period: str = "all"):
    now = datetime.utcnow()
    days_map = {"day": 1, "month": 30, "year": 365}
    cutoff = now - timedelta(days=days_map.get(period, 9999))

    cached = await get_cached_articles(product)
    filtered = []
    for a in cached:
        try:
            pub_date = datetime.fromisoformat(a.get("date", "").replace("Z", "+00:00"))
            if pub_date >= cutoff:
                filtered.append(a)
        except:
            pass

    if filtered:
        print(f"🗃️ Serving {len(filtered)} cached results for {product} ({period})")
        return JSONResponse(content=filtered)

    news = await fetch_news(product, limit=10)
    for n in news:
        n["summary"] = await ai_summarize(n.get("summary") or n["title"])
        await insert_article(product, n)

    print(f"💾 Cached {len(news)} new articles for {product}")
    return JSONResponse(content=news)


# ======================================
# 🔌 WEBSOCKET ENDPOINT
# ======================================
@app.websocket("/ws/updates")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connections.append(ws)
    print("🟢 WebSocket client connected")
    try:
        while True:
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        print("🔴 Client disconnected")
        connections.remove(ws)
    except Exception as e:
        print(f"⚠️ WebSocket error: {e}")
        if ws in connections:
            connections.remove(ws)


# ======================================
# 🔁 BACKGROUND LIVE BROADCAST
# ======================================
async def broadcast_live_news():
    topics = [
        "PFAS",
        "Activated Carbon",
        "Sustainability",
        "Energy Storage",
        "Water Treatment",
        "Mining",
        "Carbon Capture",
        "Electric Vehicles",
    ]
    i = 1
    while True:
        for topic in topics:
            news = await fetch_news(topic, limit=1)
            if not news:
                continue

            update = {
                "id": i,
                "topic": topic,
                "title": news[0]["title"],
                "source": news[0]["source"],
                "date": news[0]["date"],
                "summary": news[0]["summary"],
                "link": news[0]["link"],
            }

            disconnected = []
            for ws in connections:
                try:
                    await ws.send_text(json.dumps(update))
                except:
                    disconnected.append(ws)

            for ws in disconnected:
                connections.remove(ws)

            print(f"📡 Broadcasted update #{i}: {topic}")
            i += 1

        await asyncio.sleep(600)  # every 10 min


# ======================================
# 💬 CHAT ENDPOINT
# ======================================
@app.post("/chat")
async def chat_endpoint(request: Request):
    body = await request.json()
    user_message = body.get("message", "").strip()
    product = body.get("product", "General")

    if not user_message:
        return JSONResponse({"response": "Please enter a question."}, status_code=400)

    cached_articles = await get_cached_articles(product)
    context_text = "\n".join(
        [f"{a['title']}: {a['summary']}" for a in cached_articles[:5]]
    ) or "No recent data available."

    prompt = f"""
    You are Haycarb's AI Market Assistant.
    The user is asking about: {product}
    Use this context if relevant:
    {context_text}

    Now answer clearly and insightfully:
    {user_message}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional market research assistant."},
                {"role": "user", "content": prompt},
            ],
        )
        ai_reply = response.choices[0].message.content.strip()
        return {"response": ai_reply}
    except Exception as e:
        print("⚠️ AI Error:", e)
        return {"response": "Sorry, I couldn’t process your request right now."}


# ======================================
# 🚀 STARTUP
# ======================================
@app.on_event("startup")
async def start_background():
    await init_db()
    asyncio.create_task(broadcast_live_news())
    print("🚀 Background tasks started — CurrentsAPI + GNews + AI ready")


@app.get("/health")
def health():
    return {"ok": True, "service": "HAYCARB Market Scout API"}
