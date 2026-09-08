@echo off
rem Dev mode: start FastAPI backend + Vite frontend (hot reload) together.
rem NOTE: keep this file ASCII-only with CRLF endings -- cmd.exe misparses
rem batch files containing non-ASCII text (breaks lines mid-token).
cd /d %~dp0
start "WorkShop Backend (FastAPI :8321)" cmd /k ".venv\Scripts\python.exe backend\run.py"
start "WorkShop Frontend (Vite :5173)" cmd /k "cd frontend && npm run dev"
echo Two windows started: backend http://127.0.0.1:8321 , frontend http://127.0.0.1:5173
