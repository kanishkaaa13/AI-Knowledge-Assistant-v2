@echo off
echo Starting Ollama...
start "Ollama" cmd /k "ollama serve"
timeout /t 8

echo Killing any process on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a 2>nul
)
timeout /t 2

echo Starting Backend...
start "Backend" cmd /k "cd /d "%~dp0backend" && .venv\Scripts\activate && uvicorn app.main:app --host 127.0.0.1 --port 8000"
timeout /t 5

echo Starting Frontend...
start "Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo Done. Check each window for errors.
pause
