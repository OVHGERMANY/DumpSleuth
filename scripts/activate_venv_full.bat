@echo off
:: Simple script to activate the virtual environment
:: Run this before using the dump analysis tools

echo.
echo ================================================================
echo              ACTIVATING VIRTUAL ENVIRONMENT
echo ================================================================
echo.

if not exist ".venv" (
    echo ERROR: Virtual environment not found!
    echo TIP: Run 'python -m venv .venv' first to create it
    pause
    exit /b 1
)

echo SUCCESS: Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo ================================================================
echo           VIRTUAL ENVIRONMENT ACTIVATED
echo ================================================================
echo.
echo You can now run:
echo   - python dump_analyzer.py
echo   - python manual_analysis.py  
echo   - python string_extractor.py
echo.
echo To deactivate: type 'deactivate'
echo ================================================================ 