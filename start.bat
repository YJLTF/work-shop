@echo off
rem Run the full site like the packaged exe: venv Python serves the built frontend.
rem Run scripts\build.bat once first (or: cd frontend && npm run build).
rem NOTE: keep this file ASCII-only with CRLF endings -- cmd.exe misparses
rem batch files containing non-ASCII text (breaks lines mid-token).
cd /d %~dp0
.venv\Scripts\python.exe backend\run.py
pause
