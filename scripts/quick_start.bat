@echo off
:: Quick Start Batch File for Memory Dump Analysis
:: This script makes it easy to run the analysis tools

title DumpSleuth - Quick Start

:: Set UTF-8 encoding for better Unicode support
chcp 65001 >nul 2>&1

echo.
echo ================================================================
echo                     DUMP SLEUTH
echo                Memory Dump Analysis
echo ================================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo TIP: Please install Python 3.7+ from https://python.org
    echo NOTE: Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

:: Check if dump file exists
if not exist "*.dmp" (
    echo ERROR: No .dmp files found in current directory
    echo TIP: Make sure your dump file is in the same folder as this script
    echo Current directory: %CD%
    pause
    exit /b 1
)

echo SUCCESS: Python found
for %%f in (*.dmp) do (
    echo SUCCESS: Dump file found: %%f
)

echo.
echo Analysis Options:
echo.
echo   1. Automated Analysis (Recommended for beginners)
echo   2. Manual Analysis (Interactive exploration)
echo   3. String Extraction (Find readable text)
echo   4. Install Dependencies (First time setup)
echo   5. Test Encoding Fix (If you saw garbled characters)
echo   6. View Help/Documentation
echo   7. Exit
echo.

set /p choice="Select option (1-7): "

if "%choice%"=="1" goto automated
if "%choice%"=="2" goto manual
if "%choice%"=="3" goto strings
if "%choice%"=="4" goto install
if "%choice%"=="5" goto test_encoding
if "%choice%"=="6" goto help
if "%choice%"=="7" goto exit

echo ERROR: Invalid choice. Please select 1-7.
pause
goto :eof

:automated
echo.
echo Starting Automated Analysis...
echo This will analyze your dump file and create a detailed report
echo.
python analyzer/dump_analyzer.py
pause
goto :eof

:manual
echo.
echo Starting Manual Analysis...
echo This provides an interactive interface to explore the dump
echo.
python analyzer/manual_analysis.py
pause
goto :eof

:strings
echo.
echo Starting String Extraction...
echo This will extract all readable text from the dump file
echo.
python analyzer/string_extractor.py
pause
goto :eof

:install
echo.
echo Installing Dependencies...
echo This will install all required Python packages
echo.
pip install -r scripts/requirements.txt
if errorlevel 1 (
    echo ERROR: Installation failed. Check your internet connection and try again.
    echo TIP: You may need to run as Administrator
) else (
    echo SUCCESS: Dependencies installed successfully!
)
pause
goto :eof

:test_encoding
echo.
echo Testing Encoding Fix...
echo This will test if the character encoding issues are resolved
echo.
python analyzer/test_encoding.py
pause
goto :eof

:help
echo.
echo Opening Documentation...
start docs/README.md
echo TIP: If README doesn't open automatically, open it manually
echo Location: %CD%\docs\README.md
echo.
echo Quick Tips:
echo   - Start with option 1 (Automated Analysis) if you're new
echo   - Use option 2 (Manual Analysis) to explore specific areas
echo   - Option 3 (String Extraction) is great for finding text clues
echo   - Check the reports folder for saved reports
echo.
pause
goto :eof

:exit
echo.
echo Thanks for using DumpSleuth!
echo Check the reports folder for any saved reports
echo Run this script again anytime to analyze more dumps
echo.
pause
exit /b 0 