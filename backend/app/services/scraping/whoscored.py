import asyncio
from datetime import datetime
from typing import Dict, Optional
import httpx
from bs4 import BeautifulSoup
from ..core.config import settings


class WhoScoredScraper:
    BASE = "https://www.whoscored.com"
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "en-GB,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.whoscored.com/",
    }
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0, headers=self.HEADERS)
        self._last_request = 0
    
    async def _rate_limit(self):
        import time
        elapsed = time.time() - self._last_request
        delay = 8.0 + (15.0 - 8.0) * 0.5
        if elapsed < delay:
            await asyncio.sleep(delay - elapsed)
        self._last_request = time.time()
    
    async def get_team_tactics(self, team_name: str, team_id: str = None) -> Dict:
        """Get tactical information for a team (scrape weekly only)"""
        await self._rate_limit()
        
        try:
            search_url = f"{self.BASE}/Teams/{team_id}/{team_name.replace(' ', '-')}" if team_id else f"{self.BASE}/Search/?q={team_name}"
            
            resp = await self.client.get(search_url)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            tactics = {
                "formation_most_used": "",
                "avg_rating_home": 0.0,
                "avg_rating_away": 0.0,
                "possession_style": "unknown",
                "attacking_width": "unknown",
                "pressing_intensity": 0,
                "source": "whoscored",
                "scraped_at": datetime.utcnow().isoformat(),
            }
            
            # Extract formation
            formation_elem = soup.find('div', class_='formation')
            if formation_elem:
                tactics["formation_most_used"] = formation_elem.get_text(strip=True)
            
            # Extract average ratings
            ratings = soup.find_all('span', class_='rating')
            if len(ratings) >= 2:
                try:
                    tactics["avg_rating_home"] = float(ratings[0].get_text(strip=True))
                    tactics["avg_rating_away"] = float(ratings[1].get_text(strip=True))
                except:
                    pass
            
            # Rough possession style detection
            possession_text = soup.get_text().lower()
            if 'possessions' in possession_text:
                if 'high possession' in possession_text or 'dominant possession' in possession_text:
                    tactics["possession_style"] = "possession_based"
                elif 'counter' in possession_text:
                    tactics["possession_style"] = "counter_attack"
                else:
                    tactics["possession_style"] = "mixed"
            
            return tactics
        except Exception as e:
            print(f"WhoScored tactics error: {e}")
            return {}
    
    async def get_formation_stats(self, league_id: str) -> Dict:
        """Get formation usage stats for a league"""
        await self._rate_limit()
        
        url = f"{self.BASE}/Leagues/{league_id}/"
        
        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            formations = {}
            
            table = soup.find('table', id='formation-statistics')
            if table and table.find('tbody'):
                for row in table.find('tbody').find_all('tr'):
                    try:
                        cols = row.find_all('td')
                        if len(cols) >= 2:
                            formation = cols[0].get_text(strip=True)
                            count = int(cols[1].get_text(strip=True))
                            formations[formation] = count
                    except:
                        continue
            
            return {
                "formations": formations,
                "source": "whoscored",
                "scraped_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            print(f"WhoScored formation stats error: {e}")
            return {}
    
    async def health_check(self) -> bool:
        """Check if WhoScored is accessible"""
        try:
            await self._rate_limit()
            resp = await self.client.get(f"{self.BASE}/")
            return resp.status_code == 200
        except:
            return False
    
    async def close(self):
        await self.client.aclose()
