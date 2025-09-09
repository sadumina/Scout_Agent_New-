from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from database.models import SessionLocal, Opportunity
import asyncio

app = FastAPI()

# Allow React frontend (localhost:3000) to talk to FastAPI (localhost:8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in production, lock this down
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST endpoint (for polling)
@app.get("/opportunities")
def get_opportunities():
    db = SessionLocal()
    opps = (
        db.query(Opportunity)
        .order_by(Opportunity.date.desc())
        .limit(20)
        .all()
    )
    return [
        {
            "id": o.id,
            "title": o.title,
            "summary": o.summary,
            "source": o.source,
            "date": str(o.date),
            "link": o.link,
        }
        for o in opps
    ]


# WebSocket endpoint (for real-time push updates)
@app.websocket("/ws/opportunities")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        db = SessionLocal()
        opps = (
            db.query(Opportunity)
            .order_by(Opportunity.date.desc())
            .limit(20)
            .all()
        )
        data = [
            {
                "id": o.id,
                "title": o.title,
                "summary": o.summary,
                "source": o.source,
                "date": str(o.date),
                "link": o.link,
            }
            for o in opps
        ]
        await websocket.send_json(data)
        await asyncio.sleep(10)  # push every 10 seconds
