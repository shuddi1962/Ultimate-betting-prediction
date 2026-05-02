import asyncio
from datetime import datetime
from typing import List, Dict, Optional
import httpx
from bs4 import BeautifulSoup
from ..core.config import settings


class FotMobScraper:
    BASE = "https://www.fotmob.com/api"
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://www.fotmob.com",
        "Accept": "application/json",
        "x-fm-req": "eyJjbGllbnRUaW1lIjoiMjAyNC0wMS0wMVQwMDowMDowMC4wMDBaIn0=",
    }
    
    LEAGUE_IDS = {
        "epl": 47, "la_liga": 87, "bundesliga": 54, "serie_a": 55,
        "ligue_1": 53, "champions_league": 42, "europa_league": 73,
        "eredivisie": 57, "primeira_liga": 61, "afcon": 77,
        "npfl": 374, "psl_sa": 305, "ghana_premier": 302,
    }
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0, headers=self.HEADERS)
        self._last_request = 0
    
    async def _rate_limit(self):
        import time
        elapsed = time.time() - self._last_request
        delay = 3.0
        if elapsed < delay:
            await asyncio.sleep(delay - elapsed)
        self._last_request = time.time()
    
    async def get_fixtures_by_date(self, date: str) -> List[Dict]:
        """Get fixtures for a date (YYYYMMDD format)"""
        await self._rate_limit()
        
        url = f"{self.BASE}/matches?date={date.replace('-', '')}"
        
        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            data = resp.json()
            
            fixtures = []
            for match in data.get("matches", []):
                try:
                    fixtures.append({
                        "id": str(match.get("id", "")),
                        "home_team": match.get("home", {}).get("name", ""),
                        "away_team": match.get("away", {}).get("name", ""),
                        "home_score": match.get("home", {}).get("score", None),
                        "away_score": match.get("away", {}).get("score", None),
                        "status": match.get("status", {}).get("type", ""),
                        "kickoff": match.get("status", {}).get("utcTime", ""),
                        "league": match.get("leagueName", ""),
                        "league_id": match.get("leagueId", ""),
                        "source": "fotmob",
                        "scraped_at": datetime.utcnow().isoformat(),
                    })
                except Exception as e:
                    print(f"Parse FotMob fixture error: {e}")
                    continue
            
            return fixtures
        except Exception as e:
            print(f"FotMob fixtures error: {e}")
            return []
    
    async def get_match_details(self, match_id: str) -> Dict:
        """Get detailed match data including stats, timeline, lineups"""
        await self._rate_limit()
        
        url = f"{self.BASE}/matchDetails?matchId={match_id}"
        
        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            data = resp.json()
            
            match_data = data.get("match", {})
            
            stats = {}
            if "stats" in match_data:
                for stat in match_data.get("stats", []):
                    stats[stat.get("statName", "").lower().replace(" ", "_")] = stat.get("stats", [0, 0])
            
            timeline = match_data.get("timeline", [])
            
            lineups = {}
            if "lineups" in match_data:
                lineups = match_data.get("lineups", {})
            
            return {
                "match_id": match_id,
                "stats": stats,
                "timeline": timeline,
                "lineups": lineups,
                "xg_home": stats.get("expected_goals", [0, 0])[0] if isinstance(stats.get("expected_goals"), list) else 0,
                "xg_away": stats.get("expected_goals", [0, 0])[1] if isinstance(stats.get("expected_goals"), list) else 0,
                "source": "fotmob",
                "scraped_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            print(f"FotMob match details error: {e}")
            return {}
    
    async def get_league_standings(self, league: str) -> List[Dict]:
        """Get league standings"""
        await self._rate_limit()
        
        league_id = self.LEAGUE_IDS.get(league)
        if not league_id:
            return []
        
        url = f"{self.BASE}/leagues?id={league_id}&ccode=global&type=league&timeZone=UTC"
        
        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            data = resp.json()
            
            standings = []
            for table in data.get("tables", []):
                for idx, team in enumerate(table.get("data", {}).get("table", []), 1):
                    standings.append({
                        "position": idx,
                        "team_name": team.get("name", ""),
                        "played": team.get("played", 0),
                        "wins": team.get("wins", 0),
                        "draws": team.get("draws", 0),
                        "losses": team.get("losses", 0),
                        "goals_for": team.get("goalsFor", 0),
                        "goals_against": team.get("goalsAgainst", 0),
                        "points": team.get("pts", 0),
                        "source": "fotmob",
                        "scraped_at": datetime.utcnow().isoformat(),
                    })
            
            return standings
        except Exception as e:
            print(f"FotMob standings error: {e}")
            return []
    
    async def get_team_stats(self, team_id: str) -> Dict:
        """Get team overview and recent form"""
        await self._rate_limit()
        
        url = f"{self.BASE}/teams?id={team_id}&tab=overview&type=team&timeZone=UTC"
        
        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            data = resp.json()
            
            team_data = data.get("team", {})
            
            return {
                "name": team_data.get("name", ""),
                "recent_results": team_data.get("recentMatches", []),
                "upcoming": team_data.get("upcomingMatches", []),
                "source": "fotmob",
                "scraped_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            print(f"FotMob team stats error: {e}")
            return {}
    
    async def health_check(self) -> bool:
        """Check if FotMob is accessible"""
        try:
            await self._rate_limit()
            resp = await self.client.get(f"{self.BASE}/matches?date=20240101")
            return resp.status_code == 200
        except:
            return False
    
    async def close(self):
        await self.client.aclose()
