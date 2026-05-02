import asyncio
import re
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, List
import httpx
from bs4 import BeautifulSoup
from ..core.config import settings


class FBrefScraper:
    BASE = "https://fbref.com"
    
    FBREF_COMP_IDS = {
        "epl": 9, "la_liga": 12, "bundesliga": 20, "serie_a": 11,
        "ligue_1": 13, "champions_league": 8, "europa_league": 19,
        "eredivisie": 23, "primeira_liga": 32, "brasileirao": 24,
        "argentina": 21, "mls": 22,
    }
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept-Language": "en-GB,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
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
    
    async def get_season_stats(self, league: str, season: int = None) -> List[Dict]:
        """Get season stats for all teams in a league"""
        await self._rate_limit()
        
        cid = self.FBREF_COMP_IDS.get(league)
        if not cid:
            return []
        
        if not season:
            season = datetime.utcnow().year
        
        url = f"{self.BASE}/en/comps/{cid}/stats/Big-5-European-Leagues-Stats"
        
        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            
            tables = pd.read_html(resp.text, flavor="bs4")
            
            if not tables:
                return []
            
            df = tables[0]
            df = df.dropna(axis=1, how='all')
            
            teams = []
            for _, row in df.iterrows():
                team_name = str(row.get('Squad', row.get('Team', ''))).strip()
                if not team_name or team_name == 'nan':
                    continue
                
                teams.append({
                    "team_name": team_name,
                    "xg_for": float(row.get('xG', row.get('Expected Goals (xG)', 0) or 0),
                    "xg_against": float(row.get('xGA', row.get('Expected Goals Against (xGA)', 0) or 0),
                    "npxg": float(row.get('NPxG', row.get('Non-Penalty xG', 0) or 0),
                    "npxg_against": float(row.get('NPxGA', 0) or 0),
                    "ppda": float(row.get('PPDA', row.get('Passes Per Defensive Action', 0) or 0),
                    "shots_for": float(row.get('Shots', row.get('Shots Total', 0) or 0),
                    "shots_on_target": float(row.get('SoT', row.get('Shots on Target', 0) or 0),
                    "goals_minus_xg": float(row.get('G-xG', 0) or 0),
                    "deep_completions": float(row.get('PassLive', row.get('Passes into Penalty Area', 0) or 0),
                    "progressive_passes": float(row.get('PrgP', 0) or 0),
                    "possession": float(row.get('Poss', 0) or 0),
                    "source": "fbref",
                    "scraped_at": datetime.utcnow().isoformat(),
                })
            
            return teams
        except Exception as e:
            print(f"FBref season stats error: {e}")
            return []
    
    async def get_team_xg_history(self, team_slug: str, league: str) -> List[Dict]:
        """Get xG history for a specific team"""
        await self._rate_limit()
        
        url = f"{self.BASE}/en/squads/{team_slug}/"
        
        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            tables = pd.read_html(resp.text, flavor="bs4")
            
            matches = []
            for table in tables:
                if 'Date' not in table.columns:
                    continue
                
                for _, row in table.iterrows():
                    try:
                        xg_for = float(row.get('xG', 0) or 0)
                        xg_against = float(row.get('xGA', 0) or 0)
                        
                        matches.append({
                            "date": str(row.get('Date', '')),
                            "opponent": str(row.get('Opponent', '')),
                            "result": str(row.get('Result', '')),
                            "xg_for": xg_for,
                            "xg_against": xg_against,
                            "goals_for": float(row.get('GF', 0) or 0),
                            "goals_against": float(row.get('GA', 0) or 0),
                            "source": "fbref",
                        })
                    except Exception:
                        continue
            
            return matches[-10:] if matches else []
        except Exception as e:
            print(f"FBref team history error: {e}")
            return []
    
    async def get_league_standings(self, league: str) -> List[Dict]:
        """Get league standings with xG columns"""
        await self._rate_limit()
        
        cid = self.FBREF_COMP_IDS.get(league)
        if not cid:
            return []
        
        url = f"{self.BASE}/en/comps/{cid}/table/"
        
        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            
            tables = pd.read_html(resp.text, flavor="bs4")
            if not tables:
                return []
            
            df = tables[0]
            standings = []
            
            for idx, row in df.iterrows():
                standings.append({
                    "position": idx + 1,
                    "team_name": str(row.get('Squad', row.get('Team', ''))).strip(),
                    "played": int(row.get('MP', 0) or 0),
                    "wins": int(row.get('W', 0) or 0),
                    "draws": int(row.get('D', 0) or 0),
                    "losses": int(row.get('L', 0) or 0),
                    "goals_for": int(row.get('GF', 0) or 0),
                    "goals_against": int(row.get('GA', 0) or 0),
                    "points": int(row.get('Pts', 0) or 0),
                    "xg": float(row.get('xG', 0) or 0),
                    "xga": float(row.get('xGA', 0) or 0),
                    "source": "fbref",
                    "scraped_at": datetime.utcnow().isoformat(),
                })
            
            return standings
        except Exception as e:
            print(f"FBref standings error: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check if FBref is accessible"""
        try:
            await self._rate_limit()
            resp = await self.client.get(f"{self.BASE}/en/comps/9/stats/")
            return resp.status_code == 200
        except:
            return False
    
    async def close(self):
        await self.client.aclose()
