#!/bin/bash
# Test script for FootballIQ Pro
# Run this once Python and Docker are available

echo "FootballIQ Pro - System Test"
echo "================================"

# Check Python
echo -n "Python 3.11+ installed: "
python --version 2>/dev/null || echo "NOT FOUND"

# Check Docker
echo -n "Docker installed: "
docker --version 2>/dev/null || echo "NOT FOUND"

# Check Node.js
echo -n "Node.js installed: "
node --version 2>/dev/null || echo "NOT FOUND"

# Check if frontend dependencies installed
echo -n "Frontend dependencies: "
if [ -d "frontend/node_modules" ]; then
    echo "INSTALLED"
else
    echo "NOT INSTALLED - Run: cd frontend && npm install"
fi

# Check if backend dependencies installed
echo -n "Backend virtual environment: "
if [ -d "backend/venv" ]; then
    echo "EXISTS"
else
    echo "NOT FOUND - Run: cd backend && python -m venv venv"
fi

echo ""
echo "Next Steps:"
echo "1. Install Python 3.11+ from python.org"
echo "2. Install Docker Desktop from docker.com"
echo "3. Run: cd backend && python -m venv venv && venv\\Scripts\\activate && pip install -r requirements.txt"
echo "4. Run: docker compose up -d postgres redis"
echo "5. Run: cd backend && alembic upgrade head"
echo "6. Run: cd backend && uvicorn app.main:app --reload"
echo "7. Run: cd frontend && npm run dev"
echo ""
echo "Or simply run: setup.bat (Windows)"
