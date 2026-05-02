import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.scraping.sofascore import SofascoreScraper
from app.services.scraping.fotmob import FotMobScraper
from app.services.prediction.engine import PredictionEngine
from app.models import Fixture, Prediction


class DataRouter:
    """Routes data requests to best available source with fallback"""
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        self.sofascore = SofascoreScraper()
        self.fotmob = FotMobScraper()
        self.prediction_engine = PredictionEngine(self.db)
    
    async def get_fixtures(self, date: str = None) -> List[Dict]:
        """Get fixtures with fallback chain"""
        if not date:
            date = datetime.utcnow().strftime("%Y-%m-%d")
        
        try:
            fixtures = await self.sofascore.get_fixtures_by_date(date)
            if fixtures:
                return self._tag_source(fixtures, "sofascore")
        except Exception as e:
            print("Sofascore fixtures failed: {}".format(e))
        
        try:
            fotmob_date = date.replace("-", "")
            fixtures = await self.fotmob.get_fixtures_by_date(fotmob_date)
            if fixtures:
                return self._tag_source(fixtures, "fotmob")
        except Exception as e:
            print("FotMob fixtures failed: {}".format(e))
        
        return []
    
    async def get_live_matches(self) -> List[Dict]:
        """Get live matches from primary sources"""
        try:
            return await self.sofascore.get_live_matches()
        except Exception as e:
            print("Sofascore live failed: {}".format(e))
            try:
                return await self.fotmob.get_live_scores()
            except Exception as e2:
                print("FotMob live failed: {}".format(e2))
                return []
    
    async def get_match_stats(self, match_id: str) -> Dict:
        """Get match statistics with parallel fetches"""
        try:
            results = await asyncio.gather(
                self.sofascore.get_match_stats(match_id),
                self.sofascore.get_match_incidents(match_id),
                self.sofascore.get_lineups(match_id),
                return_exceptions=True
            )
            
            stats = results[0] if not isinstance(results[0], Exception) else {}
            incidents = results[1] if not isinstance(results[1], Exception) else []
            lineups = results[2] if not isinstance(results[2], Exception) else {}
            
            return {
                "stats": stats,
                "incidents": incidents,
                "lineups": lineups,
                "source": "sofascore",
            }
        except Exception as e:
            print("Match stats error: {}".format(e))
            return {}
    
    async def generate_prediction_for_fixture(self, fixture_id: int) -> Optional[Prediction]:
        """Generate prediction using all available scrapped data"""
        fixture = self.db.query(Fixture).filter(Fixture.id == fixture_id).first()
        if not fixture:
            return None
        
        sources_used = ["sofascore", "fbref", "transfermarkt"]
        return self.prediction_engine.generate_prediction(fixture, sources_used)
    
    def _tag_source(self, data: list, source: str) -> list:
        """Add source metadata to data"""
        timestamp = datetime.utcnow().isoformat()
        if isinstance(data, list):
            result = []
            for d in data:
                d["_source"] = source
                d["_scraped_at"] = timestamp
                result.append(d)
            return result
        return data
    
    async def health_check(self) -> Dict:
        """Check health of all scrapers"""
        results = {}
        try:
            results["sofascore"] = await self.sofascore.health_check()
        except:
            results["sofascore"] = False
        try:
            results["fotmob"] = await self.fotmob.health_check()
        except:
            results["fotmob"] = False
        return results
    
    async def close(self):
        """Close all scraper sessions"""
        await asyncio.gather(
            self.sofascore.close(),
            self.fotmob.close(),
            return_exceptions=True
        )
