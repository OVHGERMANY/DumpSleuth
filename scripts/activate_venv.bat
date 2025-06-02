@echo off
if exist .venv\Scripts\activate (
    call .venv\Scripts\activate
    pip install -r scripts/requirements.txt
) else (
    echo Virtual environment not found. Run setup_env.bat first.
) 