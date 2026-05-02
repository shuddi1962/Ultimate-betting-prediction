import asyncio
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import httpx
from bs4 import BeautifulSoup
from ..core.config import settings


class BBCSportScraper:
    BASE = "https://www.bbc.co.uk/sport/football"
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "en-GB,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    
    KEYWORDS = [
        "ruled out", "will miss", "doubt", "doubtful", "injured",
        "suspended", "returns", "fit to play", "available",
        "unlikely to feature", "expected to be fit", "training",
        "confirmed absent", "late fitness test", "injury update",
        "sidelined", "out for", "back in training",
    ]
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0, headers=self.HEADERS)
        self._last_request = 0
        self.nlp = None
    
    async def _rate_limit(self):
        import time
        elapsed = time.time() - self._last_request
        delay = settings.SCRAPE_DELAY_MIN + (settings.SCRAPE_DELAY_MAX - settings.SCRAPE_DELAY_MIN) * 0.5
        if elapsed < delay:
            await asyncio.sleep(delay - elapsed)
        self._last_request = time.time()
    
    async def _load_nlp(self):
        """Load spaCy model for NER (lazy load)"""
        if self.nlp:
            return self.nlp
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
            return self.nlp
        except Exception as e:
            print(f"spaCy load error: {e}")
            return None
    
    async def get_team_news(self, team_name: str) -> List[Dict]:
        """Get recent news for a team, focusing on injuries/availability"""
        await self._rate_limit()
        
        search_url = f"{self.BASE}/teams/{team_name.replace(' ', '-').lower()}"
        
        try:
            resp = await self.client.get(search_url)
            if resp.status_code != 200:
                return []
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            news_items = []
            
            for article in soup.find_all('article', limit=10):
                try:
                    link = article.find('a')
                    if not link:
                        continue
                    
                    title = link.get_text(strip=True)
                    href = link.get('href', '')
                    if not href.startswith('http'):
                        href = f"https://www.bbc.co.uk{href}"
                    
                    # Check if any keywords in title
                    title_lower = title.lower()
                    if not any(kw in title_lower for kw in self.KEYWORDS):
                        continue
                    
                    # Fetch article content
                    article_data = await self._fetch_article(href, team_name)
                    if article_data:
                        news_items.append(article_data)
                except Exception:
                    continue
            
            return news_items
        except Exception as e:
            print(f"BBC Sport team news error: {e}")
            return []
    
    async def _fetch_article(self, url: str, team_name: str) -> Optional[Dict]:
        """Fetch and parse a single article"""
        await self._rate_limit()
        
        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Extract article text
            article_body = soup.find('article')
            if not article_body:
                return None
            
            paragraphs = article_body.find_all('p')
            text = ' '.join(p.get_text(strip=True) for p in paragraphs)
            
            # Extract player names using NER
            nlp = await self._load_nlp()
            players = []
            if nlp:
                doc = nlp(text)
                players = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
            
            # Determine status
            text_lower = text.lower()
            status = "unknown"
            if any(kw in text_lower for kw in ["ruled out", "out for", "sidelined", "confirmed absent"]):
                status = "out"
            elif any(kw in text_lower for kw in ["doubt", "doubtful", "unlikely to feature", "late fitness test"]):
                status = "doubt"
            elif any(kw in text_lower for kw in ["returns", "fit to play", "available", "expected to be fit", "back in training"]):
                status = "available"
            
            return {
                "team": team_name,
                "title": soup.find('h1').get_text(strip=True) if soup.find('h1') else "",
                "status": status,
                "players_mentioned": players[:5],
                "url": url,
                "published_at": datetime.utcnow().isoformat(),
                "source": "bbc_sport",
                "scraped_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            print(f"BBC article fetch error: {e}")
            return None
    
    async def get_latest_injuries(self, team_name: str) -> List[Dict]:
        """Get only injury-related news"""
        news = await self.get_team_news(team_name)
        return [n for n in news if n.get("status") in ["out", "doubt"]]
    
    async def health_check(self) -> bool:
        """Check if BBC Sport is accessible"""
        try:
            await self._rate_limit()
            resp = await self.client.get(f"{self.BASE}/")
            return resp.status_code == 200
        except:
            return False
    
    async def close(self):
        await self.client.aclose()
