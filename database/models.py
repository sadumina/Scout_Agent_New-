from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./market_scout.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    source = Column(String, nullable=True)
    date = Column(DateTime, default=datetime.utcnow)
    link = Column(String, unique=True, nullable=False)
    product = Column(String, nullable=True)

Base.metadata.create_all(bind=engine)

def get_opportunities(product: str = None):
    db = SessionLocal()
    try:
        query = db.query(Opportunity)
        if product:
            query = query.filter(func.lower(Opportunity.product) == product.lower())
        rows = query.all()

        results = []
        for opp in rows:
            results.append({
                "id": opp.id,
                "title": opp.title,
                "summary": opp.summary,
                "source": opp.source,
                "date": opp.date.isoformat() if opp.date else None,
                "link": opp.link,
                "product": opp.product,
            })
        return results
    finally:
        db.close()
