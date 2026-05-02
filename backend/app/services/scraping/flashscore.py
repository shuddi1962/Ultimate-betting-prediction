import asyncio
from datetime import datetime
from typing import List, Dict, Optional
import httpx
from ..core.config import settings


class FlashscoreScraper:
    BASE = "https://www.flashscore.com"
    
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
        delay = 10.0
        if elapsed < delay:
            await asyncio.sleep(delay - elapsed)
        self._last_request = time.time()
    
    async def get_live_scores(self) -> List[Dict]:
        """Get live scores - requires Playwright for JS-rendered content"""
        await self._rate_limit()
        
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                await page.goto(f"{self.BASE}/football/", wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(3000)
                
                html = await page.content()
                await browser.close()
                
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')
                
                matches = []
                for match_elem in soup.find_all('div', class_='event__match--live'):
                    try:
                        teams = match_elem.find_all('div', class_='event__team')
                        home_team = teams[0].get_text(strip=True) if len(teams) > 0 else ""
                        away_team = teams[1].get_text(strip=True) if len(teams) > 1 else ""
                        
                        score_elem = match_elem.find('div', class_='event__scores')
                        score_text = score_elem.get_text(strip=True) if score_elem else "0-0"
                        parts = score_text.split('-')
                        home_score = int(parts[0].strip()) if len(parts) > 1 and parts[0].strip().isdigit() else 0
                        away_score = int(parts[1].strip()) if len(parts) > 1 and parts[1].strip().isdigit() else 0
                        
                        minute_elem = match_elem.find('div', class_='event__time')
                        minute = minute_elem.get_text(strip=True) if minute_elem else ""
                        
                        matches.append({
                            "home_team": home_team,
                            "away_team": away_team,
                            "home_score": home_score,
                            "away_score": away_score,
                            "minute": minute,
                            "status": "live",
                            "source": "flashscore",
                            "scraped_at": datetime.utcnow().isoformat(),
                        })
                    except Exception as e:
                        print(f"Parse Flashscore match error: {e}")
                        continue
                
                return matches
        except Exception as e:
            print(f"Flashscore live scores error: {e}")
            return []
    
    async def get_fixtures(self, date: str) -> List[Dict]:
        """Get fixtures for a specific date - backup only"""
        await self._rate_limit()
        
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                url = f"{self.BASE}/football/#/date/{date.replace('-', '')}"
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(3000)
                
                html = await page.content()
                await browser.close()
                
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')
                
                fixtures = []
                for match_elem in soup.find_all('div', class_='event__match'):
                    try:
                        teams = match_elem.find_all('div', class_='event__team')
                        if len(teams) < 2:
                            continue
                        
                        fixtures.append({
                            "home_team": teams[0].get_text(strip=True),
                            "away_team": teams[1].get_text(strip=True),
                            "date": date,
                            "source": "flashscore",
                            "scraped_at": datetime.utcnow().isoformat(),
                        })
                    except Exception:
                        continue
                
                return fixtures
        except Exception as e:
            print(f"Flashscore fixtures error: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check if Flashscore is accessible"""
        try:
            await self._rate_limit()
            resp = await self.client.get(f"{self.BASE}/")
            return resp.status_code == 200
        except:
            return False
    
    async def close(self):
        await self.client.aclose()
