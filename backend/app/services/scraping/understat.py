import asyncio
import re
import json
from datetime import datetime
from typing import Optional, Dict, List
import httpx
from ..core.config import settings


class UnderstatScraper:
    BASE = "https://understat.com"
    
    LEAGUES = {
        "epl": "EPL", "la_liga": "La_liga", "bundesliga": "Bundesliga",
        "serie_a": "Serie_A", "ligue_1": "Ligue_1", "rfpl": "RFPL"
    }
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.9",
    }
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0, headers=self.HEADERS)
        self._last_request = 0
    
    async def _rate_limit(self):
        import time
        elapsed = time.time() - self._last_request
        delay = settings.SCRAPE_DELAY_MIN + (settings.SCRAPE_DELAY_MAX - settings.SCRAPE_DELAY_MIN) * 0.5
        if elapsed < delay:
            await asyncio.sleep(delay - elapsed)
        self._last_request = time.time()
    
    def _extract_json(self, html: str, var_name: str) -> Optional[dict]:
        """Extract JSON data from JavaScript variables in page"""
        pattern = rf"var\s+{var_name}\s*=\s*JSON\.parse\('(.+?)'\)"
        matches = re.findall(pattern, html, re.DOTALL)
        if not matches:
            return None
        try:
            decoded = matches[0].encode('utf-8').decode('unicode_escape')
            return json.loads(decoded)
        except Exception:
            return None
    
    async def get_league_data(self, league: str, year: int = None) -> Dict:
        """Get all team xG data for a league season"""
        await self._rate_limit()
        
        league_slug = self.LEAGUES.get(league)
        if not league_slug:
            return {}
        
        if not year:
            year = datetime.utcnow().year
        
        url = f"{self.BASE}/league/{league_slug}/{year}"
        
        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            
            teams_data = self._extract_json(resp.text, "teamsData")
            dates_data = self._extract_json(resp.text, "datesData")
            
            return {
                "teams": teams_data or {},
                "fixtures": dates_data or [],
                "source": "understat",
                "scraped_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            print(f"Understat league data error: {e}")
            return {}
    
    async def get_team_xg(self, team_name: str, year: int = None) -> List[Dict]:
        """Get xG per match for a specific team"""
        await self._rate_limit()
        
        if not year:
            year = datetime.utcnow().year
        
        url = f"{self.BASE}/team/{team_name}/{year}"
        
        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            
            matches_data = self._extract_json(resp.text, "matchesData")
            if not matches_data:
                return []
            
            results = []
            for match in matches_data:
                results.append({
                    "date": match.get("date"),
                    "xg_for": float(match.get("xG", {}).get("h", 0) if match.get("h_a") == "h" else match.get("xG", {}).get("a", 0)),
                    "xg_against": float(match.get("xG", {}).get("a", 0) if match.get("h_a") == "h" else match.get("xG", {}).get("h", 0)),
                    "goals_for": int(match.get("goals", {}).get("h", 0) if match.get("h_a") == "h" else match.get("goals", {}).get("a", 0)),
                    "goals_against": int(match.get("goals", {}).get("a", 0) if match.get("h_a") == "h" else match.get("goals", {}).get("h", 0)),
                    "result": match.get("result", ""),
                    "opponent": match.get("opponent", ""),
                    "is_home": match.get("h_a") == "h",
                })
            
            return results[-10:] if results else []
        except Exception as e:
            print(f"Understat team xG error: {e}")
            return []
    
    async def get_match_shots(self, match_id: str) -> List[Dict]:
        """Get shot map for a specific match"""
        await self._rate_limit()
        
        url = f"{self.BASE}/match/{match_id}"
        
        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            
            shots_data = self._extract_json(resp.text, "shotsData")
            if not shots_data:
                return []
            
            shots = []
            for shot in shots_data.get("h", []) + shots_data.get("a", []):
                shots.append({
                    "player": shot.get("player", ""),
                    "minute": int(shot.get("minute", 0)),
                    "xg": float(shot.get("xG", 0)),
                    "result": shot.get("result", ""),
                    "situation": shot.get("situation", ""),
                    "shot_type": shot.get("shotType", ""),
                    "x": float(shot.get("X", 0)),
                    "y": float(shot.get("Y", 0)),
                })
            
            return shots
        except Exception as e:
            print(f"Understat match shots error: {e}")
            return []
    
    async def get_rolling_xg(self, league: str, team_name: str, n: int = 5) -> Dict:
        """Calculate rolling xG average for last N matches"""
        matches = await self.get_team_xg(team_name)
        if not matches:
            return {"xg_for_avg": 0, "xg_against_avg": 0}
        
        recent = matches[-n:]
        return {
            "xg_for_avg": sum(m["xg_for"] for m in recent) / len(recent),
            "xg_against_avg": sum(m["xg_against"] for m in recent) / len(recent),
            "xg_trend": (recent[-1]["xg_for"] if len(recent) > 0 else 0) - (recent[0]["xg_for"] if len(recent) > 0 else 0),
        }
    
    async def health_check(self) -> bool:
        """Check if Understat is accessible"""
        try:
            await self._rate_limit()
            resp = await self.client.get(f"{self.BASE}/league/EPL/2024")
            return resp.status_code == 200
        except:
            return False
    
    async def close(self):
        await self.client.aclose()
