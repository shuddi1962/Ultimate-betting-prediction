@echo off
echo FootballIQ Pro Setup Script
echo =============================

echo 1. Setting up Python backend...
cd backend
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt
echo Backend dependencies installed!

echo.
echo 2. Setting up database...
set /p setup_db="Do you want to set up PostgreSQL via Docker? (y/n): "
if "%setup_db%"=="y" (
    cd ..
    docker-compose up -d postgres redis
    echo Waiting for PostgreSQL to start...
    timeout /t 10
    cd backend
    alembic upgrade head
    echo Database initialized!
)

echo.
echo 3. Setting up frontend...
cd ../frontend
npm install
echo Frontend dependencies installed!

echo.
echo =============================
echo Setup complete!
echo.
echo To start the application:
echo 1. Backend: cd backend && uvicorn app.main:app --reload
echo 2. Frontend: cd frontend && npm run dev
echo 3. Or use Docker: docker-compose up
echo.
pause
