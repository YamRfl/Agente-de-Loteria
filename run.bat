@echo off
cd /d "%~dp0"
set "SSLKEYLOGFILE="
call venv\Scripts\activate.bat
echo.
echo ^> streamlit run app.py
streamlit run app.py