@echo off
REM Test runner script for the backend (Windows)

echo Running backend tests...
echo.

cd backend

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install dependencies if needed
pip install -q -r requirements.txt

REM Run tests
echo Running pytest...
pytest tests/ -v --tb=short

echo.
echo All tests completed!

pause
