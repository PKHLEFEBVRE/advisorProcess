@echo off
REM Disable the Streamlit first-run telemetry prompt
set STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

echo Ensuring dependencies are installed...
pip install -q -r requirements.txt

echo Starting Compliance Tracker...
python -m streamlit run app.py

echo.
echo Application closed or crashed.
pause
