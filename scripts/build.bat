@echo off
rem One-click packaging: build frontend -> copy static assets -> PyInstaller exe.
rem NOTE: keep this file ASCII-only with CRLF endings -- cmd.exe misparses
rem batch files containing non-ASCII text (breaks lines mid-token).
cd /d %~dp0..
.venv\Scripts\python.exe scripts\build_exe.py %*
pause
