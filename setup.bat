@echo off
REM Setup script for Collaborative Code Editor (Windows)
REM This script sets up the development environment

echo ==========================================
echo Collaborative Code Editor - Setup Script
echo ==========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not installed. Please install Docker Desktop first.
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo Error: Docker Compose is not installed. Please install Docker Compose first.
    exit /b 1
)

REM Create .env files from examples
echo Creating environment files...
if not exist "backend\.env" (
    copy "backend\.env.example" "backend\.env"
    echo Created backend\.env
)

if not exist "frontend\.env" (
    copy "frontend\.env.example" "frontend\.env"
    echo Created frontend\.env
)

echo.
echo Setup complete!
echo.
echo To start the application with Docker:
echo   docker-compose up
echo.
echo To start for local development:
echo.
echo 1. Start Redis:
echo    docker run -d -p 6379:6379 redis:7-alpine
echo.
echo 2. Start Backend:
echo    cd backend
echo    python -m venv venv
echo    venv\Scripts\activate
echo    pip install -r requirements.txt
echo    uvicorn main:app --reload
echo.
echo 3. Start Frontend:
echo    cd frontend
echo    npm install
echo    npm run dev
echo.
echo Access the application at http://localhost:3000
echo API documentation at http://localhost:8000/docs

pause
