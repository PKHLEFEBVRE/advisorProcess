@echo off
REM Disable the Streamlit first-run telemetry prompt which blocks the app from starting
set STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

REM Launches the Compliance Tracker Dashboard
echo Starting Compliance Tracker...
start "" http://localhost:8501
python -m streamlit run app.py
