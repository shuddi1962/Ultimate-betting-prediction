@echo off
echo FootballIQ Pro - System Test
echo ================================

REM Check Python
python --version 2>nul
if errorlevel 1 (
    echo Python: NOT FOUND - Install from python.org
) else (
    echo Python: Installed
)

REM Check Docker
docker --version 2>nul
if errorlevel 1 (
    echo Docker: NOT FOUND - Install Docker Desktop
) else (
    echo Docker: Installed
)

REM Check Node.js
node --version 2>nul
if errorlevel 1 (
    echo Node.js: NOT FOUND - Install from nodejs.org
) else (
    echo Node.js: Installed
)

REM Check frontend
if exist "frontend\node_modules\" (
    echo Frontend deps: INSTALLED
) else (
    echo Frontend deps: NOT INSTALLED - cd frontend && npm install
)

REM Check backend venv
if exist "backend\venv\" (
    echo Backend venv: EXISTS
) else (
    echo Backend venv: NOT FOUND - cd backend && python -m venv venv
)

echo.
echo Next Steps:
echo 1. Install Python 3.11+ from python.org
echo 2. Install Docker Desktop from docker.com  
echo 3. cd backend ^&^& python -m venv venv ^&^& venv\Scripts\activate ^&^& pip install -r requirements.txt
echo 4. docker compose up -d postgres redis
echo 5. cd backend ^&^& alembic upgrade head
echo 6. cd backend ^&^& uvicorn app.main:app --reload
echo 7. cd frontend ^&^& npm run dev
echo.
echo Or simply run: setup.bat
pause
