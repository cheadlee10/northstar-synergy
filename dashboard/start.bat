@echo off
cd /d C:\Users\chead\.openclaw\workspace\dashboard
start "" cmd /k "python app.py"
timeout /t 3 /nobreak >nul
echo Dashboard running at http://localhost:8765
start http://localhost:8765
