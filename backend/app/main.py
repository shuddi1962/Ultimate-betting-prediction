from fastapi import FastAPI, HTTPException
from typing import List, Dict, Optional
import asyncio

from app.core.database import get_db
from app.services.ingestion.data_router import DataRouter
from app.models import Fixture, Prediction

app = FastAPI(title="Football Prediction API", version="1.0")

@app.get("/")
async def root():
    return {"message": "Football Prediction API - Running"}

@app.get("/api/v1/fixtures/today")
async def get_today_fixtures():
    """Get today's fixtures from scrapers"""
    router = DataRouter()
    try:
        fixtures = await router.get_fixtures()
        await router.close()
        return {"fixtures": fixtures, "count": len(fixtures)}
    except Exception as e:
        await router.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/fixtures/{date}")
async def get_fixtures_by_date(date: str):
    """Get fixtures for a specific date (YYYY-MM-DD)"""
    router = DataRouter()
    try:
        fixtures = await router.get_fixtures(date)
        await router.close()
        return {"date": date, "fixtures": fixtures, "count": len(fixtures)}
    except Exception as e:
        await router.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/live")
async def get_live_matches():
    """Get all live matches"""
    router = DataRouter()
    try:
        matches = await router.get_live_matches()
        await router.close()
        return {"live_matches": matches, "count": len(matches)}
    except Exception as e:
        await router.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/match/{match_id}/stats")
async def get_match_stats(match_id: str):
    """Get detailed stats for a match"""
    router = DataRouter()
    try:
        stats = await router.get_match_stats(match_id)
        await router.close()
        return stats
    except Exception as e:
        await router.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/health")
async def health_check():
    """Check health of all scraper sources"""
    router = DataRouter()
    try:
        health = await router.health_check()
        await router.close()
        return health
    except Exception as e:
        await router.close()
        return {"error": str(e)}

@app.get("/api/v1/leagues")
async def get_leagues(db: Session = Depends(get_db)):
    """Get all leagues"""
    from app.models import League
    leagues = db.query(League).all()
    return {"leagues": [{"id": l.id, "name": l.name, "country": l.country} for l in leagues]}

@app.get("/api/v1/analytics/summary")
async def get_analytics_summary(db: Session = Depends(get_db)):
    """Get prediction analytics summary"""
    from app.models import Prediction
    from sqlalchemy import func
    total = db.query(func.count(Prediction.id)).scalar() or 0
    avg_confidence = db.query(func.avg(Prediction.confidence_score)).scalar() or 0
    return {
        "totalPredictions": total,
        "accuracyRate": 0.0,
        "activeLeagues": 0,
        "dataSources": ["sofascore", "fotmob", "fbref", "understat", "transfermarkt"],
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
