# FootballIQ Pro - Free Football Prediction Platform

A football prediction platform that uses ONLY free web scrapers (no paid APIs).

## Features

- **Free Data Sources**: Sofascore, FotMob, FBref, Understat, Transfermarkt, and more
- **Prediction Engine**: Modified Dixon-Coles Poisson model with xG adjustment
- **Confidence Scoring**: Data completeness, model agreement, sample size metrics
- **Real-time Data**: Live scores, match stats, lineups, incidents
- **Modern Stack**: Next.js 14 + FastAPI + PostgreSQL + Redis

## Project Structure

```
football-iq-pro/
├── backend/
│   ├── app/
│   │   ├── core/          # Config, database
│   │   ├── models.py      # SQLAlchemy models
│   │   ├── services/
│   │   │   ├── scraping/ # Free scrapers (10+ sources)
│   │   │   ├── prediction/ # ML models
│   │   │   └── ingestion/ # Data router
│   │   └── main.py       # FastAPI endpoints
│   ├── alembic/           # Database migrations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/               # Next.js pages
│   │   ├── page.tsx      # Home
│   │   ├── fixtures/     # Fixtures list
│   │   ├── match/[id]/   # Match details
│   │   ├── live/         # Live scores
│   │   ├── leagues/      # Leagues
│   │   └── analytics/    # Stats
│   ├── lib/              # API client
│   └── Dockerfile
├── docker-compose.yml
├── .env                  # Config (no API keys!)
└── setup.bat            # Windows setup script
```

## Quick Start

### Option 1: Docker (Recommended)
```bash
docker-compose up -d
```

### Option 2: Manual Setup
```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

## API Endpoints

- `GET /` - API status
- `GET /api/v1/fixtures/today` - Today's fixtures
- `GET /api/v1/fixtures/{date}` - Fixtures by date
- `GET /api/v1/live` - Live matches
- `GET /api/v1/match/{id}/stats` - Match statistics
- `GET /api/v1/leagues` - All leagues
- `GET /api/v1/analytics/summary` - Analytics
- `GET /api/v1/health` - Scraper health check

## Configuration

Edit `.env` file:
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `LOG_LEVEL` - Logging level
- `SCRAPER_*` - Scraper-specific settings

## Key Principles

1. **No Paid APIs** - All data from free web scrapers
2. **No Fabricated Data** - Show "Insufficient data" if unavailable
3. **Source Attribution** - All predictions cite data sources
4. **Confidence Scores** - Every prediction has confidence metrics
5. **Rate Limiting** - Respect robots.txt and rate limits (3-7s delays)

## Technologies

- **Backend**: FastAPI, SQLAlchemy, Playwright, httpx
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Database**: PostgreSQL, Redis
- **ML**: NumPy, Pandas, scikit-learn, XGBoost
- **Scraping**: BeautifulSoup, lxml, Playwright

## Next Steps

1. Run `setup.bat` (Windows) or follow manual setup
2. Start Docker or run services manually
3. Visit http://localhost:3000 for frontend
4. Visit http://localhost:8000/docs for API docs
5. Data will populate as scrapers run

## Troubleshooting

- **Python not found**: Install Python 3.11+ and add to PATH
- **npm install fails**: Try `npm install --timeout=600000`
- **Database connection error**: Ensure PostgreSQL is running
- **Scraper errors**: Check internet connection and rate limits

## License

MIT
