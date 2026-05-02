import asyncio
from datetime import datetime
from typing import List, Dict, Optional
import httpx
from bs4 import BeautifulSoup
from ..core.config import settings


class ElevenVElevenScraper:
    BASE = "https://www.11v11.com"
    
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
    
    async def get_h2h(self, team_a_name: str, team_b_name: str) -> List[Dict]:
        """Get all-time H2H history between two teams"""
        await self._rate_limit()
        
        team_a_slug = team_a_name.lower().replace(' ', '-')
        team_b_slug = team_b_name.lower().replace(' ', '-')
        
        url = f"{self.BASE}/teams/{team_a_slug}/head2head/{team_b_slug}/"
        
        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            matches = []
            
            table = soup.find('table', class_='mctable')
            if not table or not table.find('tbody'):
                return []
            
            for row in table.find('tbody').find_all('tr'):
                try:
                    cols = row.find_all('td')
                    if len(cols) < 5:
                        continue
                    
                    date_text = cols[0].get_text(strip=True)
                    
                    home_team = cols[1].get_text(strip=True)
                    away_team = cols[2].get_text(strip=True)
                    
                    score_text = cols[3].get_text(strip=True)
                    parts = score_text.split(' - ') if ' - ' in score_text else score_text.split('-')
                    home_score = int(parts[0].strip()) if len(parts) > 1 and parts[0].strip().isdigit() else 0
                    away_score = int(parts[1].strip()) if len(parts) > 1 and parts[1].strip().isdigit() else 0
                    
                    competition = cols[4].get_text(strip=True)
                    venue = cols[5].get_text(strip=True) if len(cols) > 5 else ""
                    
                    matches.append({
                        "date": date_text,
                        "home_team": home_team,
                        "away_team": away_team,
                        "home_score": home_score,
                        "away_score": away_score,
                        "competition": competition,
                        "venue": venue,
                        "source": "11v11",
                        "scraped_at": datetime.utcnow().isoformat(),
                    })
                except Exception as e:
                    print(f"Parse 11v11 row error: {e}")
                    continue
            
            return matches
        except Exception as e:
            print(f"11v11 H2H error: {e}")
            return []
    
    async def get_h2h_summary(self, team_a_name: str, team_b_name: str) -> Dict:
        """Get H2H summary statistics"""
        matches = await self.get_h2h(team_a_name, team_b_name)
        
        if not matches:
            return {}
        
        total = len(matches)
        team_a_wins = sum(1 for m in matches if m['home_team'] == team_a_name and m['home_score'] > m['away_score'] or 
                         m['away_team'] == team_a_name and m['away_score'] > m['home_score'])
        team_b_wins = sum(1 for m in matches if m['home_team'] == team_b_name and m['home_score'] > m['away_score'] or 
                         m['away_team'] == team_b_name and m['away_score'] > m['home_score'])
        draws = sum(1 for m in matches if m['home_score'] == m['away_score'])
        
        total_goals = sum(m['home_score'] + m['away_score'] for m in matches)
        
        return {
            "total_matches": total,
            "team_a_wins": team_a_wins,
            "team_b_wins": team_b_wins,
            "draws": draws,
            "team_a_win_rate": team_a_wins / total if total > 0 else 0,
            "team_b_win_rate": team_b_wins / total if total > 0 else 0,
            "draw_rate": draws / total if total > 0 else 0,
            "avg_goals_per_match": total_goals / total if total > 0 else 0,
            "recent_matches": matches[:10],
            "source": "11v11",
        }
    
    async def health_check(self) -> bool:
        """Check if 11v11 is accessible"""
        try:
            await self._rate_limit()
            resp = await self.client.get(f"{self.BASE}/")
            return resp.status_code == 200
        except:
            return False
    
    async def close(self):
        await self.client.aclose()
