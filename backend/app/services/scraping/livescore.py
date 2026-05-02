import asyncio
from datetime import datetime
from typing import List, Dict, Optional
import httpx
from ..core.config import settings


class LivescoreScraper:
    BASE = "https://www.livescore.com/en/football/"
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "en-GB,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
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
    
    async def get_live_scores(self) -> List[Dict]:
        """Get live scores from Livescore.com"""
        await self._rate_limit()
        
        try:
            resp = await self.client.get(self.BASE)
            resp.raise_for_status()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            matches = []
            
            for match_elem in soup.find_all('div', class_='match'):
                try:
                    home_elem = match_elem.find('div', class_='team--home')
                    away_elem = match_elem.find('div', class_='team--away')
                    
                    if not home_elem or not away_elem:
                        continue
                    
                    home_team = home_elem.get_text(strip=True)
                    away_team = away_elem.get_text(strip=True)
                    
                    score_elem = match_elem.find('div', class_='score')
                    score_text = score_elem.get_text(strip=True) if score_elem else "0-0"
                    parts = score_text.split('-')
                    home_score = int(parts[0].strip()) if len(parts) > 1 and parts[0].strip().isdigit() else 0
                    away_score = int(parts[1].strip()) if len(parts) > 1 and parts[1].strip().isdigit() else 0
                    
                    status_elem = match_elem.find('div', class_='status')
                    status = status_elem.get_text(strip=True) if status_elem else "unknown"
                    
                    matches.append({
                        "home_team": home_team,
                        "away_team": away_team,
                        "home_score": home_score,
                        "away_score": away_score,
                        "status": status,
                        "source": "livescore",
                        "scraped_at": datetime.utcnow().isoformat(),
                    })
                except Exception as e:
                    print(f"Parse Livescore match error: {e}")
                    continue
            
            return matches
        except Exception as e:
            print(f"Livescore error: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check if Livescore is accessible"""
        try:
            await self._rate_limit()
            resp = await self.client.get("https://www.livescore.com")
            return resp.status_code == 200
        except:
            return False
    
    async def close(self):
        await self.client.aclose()
