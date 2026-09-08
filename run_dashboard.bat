@echo off
echo ===================================================
echo   StreamSentinel Fraud Monitoring Dashboard Launcher
echo ===================================================
cd /d "%~dp0"
py -m streamlit run dashboard.py
pause
