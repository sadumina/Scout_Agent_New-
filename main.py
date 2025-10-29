import os
import json
import asyncio
import httpx
import re
from datetime import datetime, timedelta, timezone
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from openai import OpenAI
from db import init_db, insert_article, get_cached_articles

# ======================================
# 🔧 CONFIG
# ======================================
load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
SERPER_KEY = os.getenv("SERPER_API_KEY")  # ✅ Serper API Key

app = FastAPI(title="HAYCARB Market Scout API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",                                   # LOCAL DEV
        "https://scout-agent-reimplement-websockets.vercel.app",  # ✅ FRONTEND (VERCEL)
    ],
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
        return "No summary available."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Summarize in 25 words:\n{text}"}],
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print("⚠️ Summarization skipped:", e)
        return text[:150] + "..."   # ✅ return raw text, don't crash



# ======================================
# 🌍 FETCH NEWS (Serper.dev → Google News API)
# ======================================
# ======================================
# 🌍 FETCH NEWS (Serper.dev → Google News API)
# Handles: "1 day ago", "15 minutes ago", "3 hours ago"
# ======================================

async def fetch_news(product: str, limit: int = 8):
    if not SERPER_KEY:
        print("❌ SERPER_API_KEY missing in `.env`, configure it!")
        return []

    url = "https://google.serper.dev/news"
    headers = {"X-API-KEY": SERPER_KEY}
    payload = {"q": product, "num": limit}

    async with httpx.AsyncClient() as http:
        try:
            res = await http.post(url, json=payload, headers=headers, timeout=15)
            res.raise_for_status()
        except Exception as e:
            print("❌ Serper Fetch Error:", e)
            return []

        data = res.json().get("news", [])

    news_list = []

    for a in data:
        raw_date = a.get("date", "")

        # ✅ Convert "4 minutes ago", "1 day ago", "13 hours ago" → real datetime
        if "ago" in raw_date:
            try:
                num, unit, *_ = raw_date.split()
                num = int(num)

                if "hour" in unit:
                    pub_date = datetime.now(timezone.utc) - timedelta(hours=num)
                elif "minute" in unit:
                    pub_date = datetime.now(timezone.utc) - timedelta(minutes=num)
                elif "day" in unit:
                    pub_date = datetime.now(timezone.utc) - timedelta(days=num)
                else:
                    pub_date = datetime.now(timezone.utc)
            except:
                pub_date = datetime.now(timezone.utc)
        else:
            # ✅ Try ISO format, fallback to now()
            try:
                pub_date = datetime.fromisoformat(
                    raw_date.replace("Z", "+00:00")
                )
            except:
                pub_date = datetime.now(timezone.utc)

        news_list.append({
            "title": a["title"],
            "source": a.get("source", "Unknown"),
            "date": pub_date.isoformat(),     # ✅ Always ISO datetime
            "summary": a.get("snippet", "No summary available"),
            "link": a.get("link"),
        })

    print(f"✅ SERPER returned {len(news_list)} articles for {product}")
    return news_list


# ======================================
# 📦 OPPORTUNITIES ENDPOINT (pagination + sorting + timezone FIX)
# ======================================
@app.get("/opportunities")
async def get_opportunities(
    request: Request,
    product: str,
    period: str = "all",
    skip: int = Query(0, ge=0),
    limit: int = Query(8, ge=1, le=50)
):

    now = datetime.now(timezone.utc)  # ✅ timezone-aware datetime
    days_map = {"day": 1, "month": 30, "year": 365}
    cutoff = now - timedelta(days=days_map.get(period, 9999))

    cached = await get_cached_articles(product)

    sort_order = request.query_params.get("order", "desc")  # asc = oldest first

    sorted_cached = sorted(
        cached,
        key=lambda x: x.get("date", ""),
        reverse=(sort_order == "desc"),
    )

    filtered = []
    for a in sorted_cached:
        try:
            raw_date = a.get("date", "").replace("Z", "+00:00")
            pub_date = datetime.fromisoformat(raw_date)

            if pub_date >= cutoff:
                filtered.append(a)

        except Exception as e:
            print("⚠️ Date parsing issue:", e)

    paginated = filtered[skip: skip + limit]

    if paginated:
        print(f"🗃️ Returned {len(paginated)} cached | skip={skip}, order={sort_order}")
        return JSONResponse(content=paginated)

    # ✅ Fetch new fresh updates
    news = await fetch_news(product, limit=10)

    for n in news:
        n["summary"] = await ai_summarize(n.get("summary") or n["title"])
        await insert_article(product, n)

    print(f"💾 Cached {len(news)} new articles for {product}")
    return JSONResponse(content=news)


# ======================================
# 💬 AI CHAT ENDPOINT (Assistant remains unchanged)
# ======================================
@app.post("/chat")
async def chat_endpoint(request: Request):
    body = await request.json()
    user_message = body.get("message", "").strip()
    product = body.get("product", "General")

    if not user_message:
        return JSONResponse({"response": "Please enter a question."}, status_code=400)

    cached_articles = await get_cached_articles(product)
    context = "\n".join([f"- {a['title']} ({a['summary']})" for a in cached_articles[:5]])

    prompt = f"""
You are Haycarb's AI Market Intelligence Assistant.
User is asking about: **{product}**

Latest related updates:
{context}

Respond concisely and insightfully.
User question:
{user_message}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert market insights assistant."},
                {"role": "user", "content": prompt},
            ]
        )
        return {"response": response.choices[0].message.content.strip()}

    except Exception as e:
        print("⚠️ AI chat error:", e)
        return {"response": "Something went wrong. Try again."}


# ======================================
# 🔌 WEBSOCKET — Live Push Notifications
# ======================================
@app.websocket("/ws/updates")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connections.append(ws)
    print("🟢 WS client connected")

    try:
        while True:
            await ws.receive_text()  # ✅ Fix: keeps connection alive
    except WebSocketDisconnect:
        print("🔴 WS client disconnected")
        connections.remove(ws)



# ======================================
# 🔁 BACKGROUND BROADCASTER
# ======================================
async def broadcast_live_news():
    topics = ["PFAS", "Activated Carbon", "Gold Recovery", "Water Treatment"]
    update_id = 1

    while True:
        for topic in topics:
            news = await fetch_news(topic, limit=1)
            if news:
                for ws in connections[:]:
                    try:
                        await ws.send_text(json.dumps(news[0]))
                    except:
                        connections.remove(ws)

                print(f"📡 Live Update #{update_id} sent → {topic}")
                update_id += 1

        await asyncio.sleep(600)  # every 10 minutes


# ======================================
# 🚀 STARTUP
# ======================================
@app.on_event("startup")
async def on_startup():
    await init_db()
    asyncio.create_task(broadcast_live_news())
    print("🚀 News service + AI Assistant started")


@app.get("/health")
def health_check():
    return {"healthy": True, "AI": bool(OPENAI_KEY), "News": bool(SERPER_KEY)}
