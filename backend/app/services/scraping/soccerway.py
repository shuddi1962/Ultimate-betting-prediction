import asyncio
from datetime import datetime
from typing import List, Dict, Optional
import httpx
from ..core.config import settings


class SoccerwayScraper:
    BASE = "https://int.soccerway.com"
    
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
    
    async def get_h2h(self, team_a_slug: str, team_b_slug: str, team_a_id: str = None, team_b_id: str = None) -> List[Dict]:
        """Get H2H history between two teams"""
        await self._rate_limit()
        
        try:
            if team_a_id and team_b_id:
                url = f"{self.BASE}/head2head/matches/{team_a_id}/{team_b_id}/"
            else:
                url = f"{self.BASE}/teams/{team_a_slug}/head-to-head/"
            
            resp = await self.client.get(url)
            resp.raise_for_status()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            matches = []
            table = soup.find('table', class_='matches')
            if not table or not table.find('tbody'):
                return []
            
            for row in table.find('tbody').find_all('tr'):
                try:
                    cols = row.find_all('td')
                    if len(cols) < 5:
                        continue
                    
                    date_text = cols[0].get_text(strip=True)
                    
                    teams = cols[1].find_all('a') if cols[1].find_all('a') else []
                    home_team = teams[0].get_text(strip=True) if len(teams) > 0 else ""
                    away_team = teams[1].get_text(strip=True) if len(teams) > 1 else ""
                    
                    score_text = cols[2].get_text(strip=True)
                    parts = score_text.split(' - ')
                    home_score = int(parts[0].strip()) if len(parts) > 1 and parts[0].strip().isdigit() else 0
                    away_score = int(parts[1].strip()) if len(parts) > 1 and parts[1].strip().isdigit() else 0
                    
                    competition = cols[3].get_text(strip=True)
                    venue = cols[4].get_text(strip=True)
                    
                    matches.append({
                        "date": date_text,
                        "home_team": home_team,
                        "away_team": away_team,
                        "home_score": home_score,
                        "away_score": away_score,
                        "competition": competition,
                        "venue": venue,
                        "source": "soccerway",
                        "scraped_at": datetime.utcnow().isoformat(),
                    })
                except Exception as e:
                    print(f"Parse H2H row error: {e}")
                    continue
            
            return matches[:20] if matches else []
        except Exception as e:
            print(f"Soccerway H2H error: {e}")
            return []
    
    async def get_team_h2h(self, team_slug: str) -> Dict:
        """Get H2H summary for a team"""
        await self._rate_limit()
        
        url = f"{self.BASE}/teams/{team_slug}/"
        
        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            h2h_section = soup.find('div', id='page_team_1_block_head2head_1')
            if not h2h_section:
                return {}
            
            matches = self.get_h2h(team_slug, "")
            
            if not matches:
                return {}
            
            home_wins = sum(1 for m in matches if m['home_team'].lower() in team_slug.lower() and m['home_score'] > m['away_score'])
            away_wins = sum(1 for m in matches if m['away_team'].lower() in team_slug.lower() and m['away_score'] > m['home_score'])
            draws = sum(1 for m in matches if m['home_score'] == m['away_score'])
            
            total_goals = sum(m['home_score'] + m['away_score'] for m in matches)
            
            return {
                "total_matches": len(matches),
                "home_win_rate": home_wins / len(matches) if matches else 0,
                "away_win_rate": away_wins / len(matches) if matches else 0,
                "draw_rate": draws / len(matches) if matches else 0,
                "avg_goals_per_match": total_goals / len(matches) if matches else 0,
                "recent_matches": matches[:5],
                "source": "soccerway",
            }
        except Exception as e:
            print(f"Soccerway team H2H error: {e}")
            return {}
    
    async def health_check(self) -> bool:
        """Check if Soccerway is accessible"""
        try:
            await self._rate_limit()
            resp = await self.client.get(f"{self.BASE}/")
            return resp.status_code == 200
        except:
            return False
    
    async def close(self):
        await self.client.aclose()
