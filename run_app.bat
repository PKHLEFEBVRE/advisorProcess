@echo off
REM Disable the Streamlit first-run telemetry prompt
set STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

echo Ensuring dependencies are installed...
pip install -q -r requirements.txt

REM Launch the Compliance Tracker Dashboard silently in the background
REM Using pythonw hides the console window.
start "" pythonw -m streamlit run app.py
