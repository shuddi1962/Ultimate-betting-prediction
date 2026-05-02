import asyncio
from datetime import datetime
from typing import List, Dict, Optional
import httpx
from ..core.config import settings


class TransfermarktScraper:
    BASE = "https://www.transfermarkt.com"
    
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
        delay = settings.SCRAPE_DELAY_MIN + (settings.SCRAPE_DELAY_MAX - settings.SCRAPE_DELAY_MIN) * 0.7
        if elapsed < delay:
            await asyncio.sleep(delay - elapsed)
        self._last_request = time.time()
    
    async def get_injuries(self, team_slug: str, tm_id: str) -> List[Dict]:
        """Get injury list for a team"""
        await self._rate_limit()
        
        url = f"{self.BASE}/en/{team_slug}/verletzungen/verein/{tm_id}"
        
        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            injuries = []
            table = soup.find('table', class_='items')
            if not table:
                return []
            
            for row in table.find('tbody').find_all('tr') if table.find('tbody') else []:
                try:
                    cols = row.find_all('td')
                    if len(cols) < 6:
                        continue
                    
                    player_name = cols[0].get_text(strip=True)
                    injury_type = cols[1].get_text(strip=True)
                    
                    injured_since_text = cols[2].get_text(strip=True)
                    injured_since = self._parse_date(injured_since_text)
                    
                    expected_return_text = cols[3].get_text(strip=True)
                    expected_return = self._parse_date(expected_return_text) if '?' not in expected_return_text else None
                    
                    matches_missed = int(cols[4].get_text(strip=True).rstrip('+') or 0)
                    
                    market_value_text = cols[5].get_text(strip=True).replace('€', '').replace('m', '')
                    market_value = float(market_value_text) if market_value_text.replace('.', '').isdigit() else 0.0
                    
                    injuries.append({
                        "player_name": player_name,
                        "position": "",
                        "injury_type": injury_type,
                        "injured_since": injured_since.isoformat() if injured_since else None,
                        "expected_return": expected_return.isoformat() if expected_return else None,
                        "matches_missed": matches_missed,
                        "market_value_eur": market_value * 1000000 if 'm' in cols[5].get_text() else float(market_value or 0),
                        "source": "transfermarkt",
                        "scraped_at": datetime.utcnow().isoformat(),
                    })
                except Exception as e:
                    print(f"Parse injury row error: {e}")
                    continue
            
            return injuries
        except Exception as e:
            print(f"Transfermarkt injuries error: {e}")
            return []
    
    async def get_suspensions(self, team_slug: str, tm_id: str) -> List[Dict]:
        """Get suspension list for a team"""
        await self._rate_limit()
        
        url = f"{self.BASE}/en/{team_slug}/sperrenabstrafen/verein/{tm_id}"
        
        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            suspensions = []
            table = soup.find('table', class_='items')
            if not table or not table.find('tbody'):
                return []
            
            for row in table.find('tbody').find_all('tr'):
                try:
                    cols = row.find_all('td')
                    if len(cols) < 4:
                        continue
                    
                    suspensions.append({
                        "player_name": cols[0].get_text(strip=True),
                        "reason": cols[1].get_text(strip=True),
                        "suspended_until": self._parse_date(cols[2].get_text(strip=True)).isoformat() if cols[2].get_text(strip=True) != '?' else None,
                        "matches_remaining": int(cols[3].get_text(strip=True).rstrip('+') or 0),
                        "is_suspended": True,
                        "source": "transfermarkt",
                        "scraped_at": datetime.utcnow().isoformat(),
                    })
                except Exception:
                    continue
            
            return suspensions
        except Exception as e:
            print(f"Transfermarkt suspensions error: {e}")
            return []
    
    def _parse_date(self, date_str: str):
        """Parse various date formats"""
        try:
            from datetime import datetime
            date_str = date_str.strip()
            for fmt in ['%b %d, %Y', '%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            return None
        except:
            return None
    
    async def health_check(self) -> bool:
        """Check if Transfermarkt is accessible"""
        try:
            await self._rate_limit()
            resp = await self.client.get(f"{self.BASE}/en/")
            return resp.status_code == 200
        except:
            return False
    
    async def close(self):
        await self.client.aclose()
