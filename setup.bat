@echo off
echo ==============================================
echo OralVision - Local Environment Setup
echo ==============================================

echo [1/3] Setting up Python Backend...
cd backend
if not exist ".venv" (
    python -m venv .venv
)
call .venv\Scripts\activate.bat
pip install -r requirements.txt
echo Running database migrations and seed script...
python -m app.seed
cd ..

echo [2/3] Setting up Node Frontend...
cd frontend
call npm install
cd ..

echo [3/3] Starting Servers...
echo Starting backend...
start cmd /k "cd backend && call .venv\Scripts\activate.bat && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo Starting frontend...
start cmd /k "cd frontend && npm run dev"

echo.
echo ============================================
echo  OralVision is starting up!
echo  Backend:  http://localhost:8000
echo  Frontend: http://localhost:5173
echo  API Docs: http://localhost:8000/docs
echo ============================================
echo.
echo IMPORTANT: Ensure backend\.env contains DATABASE_URL and any required keys.
echo.
pause
