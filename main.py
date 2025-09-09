from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from database.models import get_opportunities

app = FastAPI()

# ✅ must be before routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],  # allow React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/opportunities")
def fetch_opportunities(product: str = Query(default=None, description="Filter by product")):
    return get_opportunities(product)
