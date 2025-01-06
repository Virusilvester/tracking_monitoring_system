@echo off

REM Check if .venv exists
if not exist ".venv" (
    echo .venv not found. Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo Failed to create virtual environment. Exiting...
        exit /b 1
    )
    echo Virtual environment created successfully.

    REM Install dependencies on first creation
    if exist "requirements.txt" (
        echo Installing dependencies from requirements.txt...
        call .venv\Scripts\activate
        pip install -r requirements.txt
        if errorlevel 1 (
            echo Failed to install dependencies. Exiting...
            deactivate
            exit /b 1
        )
        deactivate
    ) else (
        echo requirements.txt not found. Skipping dependency installation.
    )
)

REM Activate the virtual environment
call .venv\Scripts\activate
if errorlevel 1 (
    echo Failed to activate virtual environment. Exiting...
    exit /b 1
)

REM Run the Python script
echo Running main.py...
python main.py
if errorlevel 1 (
    echo Error running main.py. Exiting...
    deactivate
    exit /b 1
)

REM Deactivate the virtual environment
deactivate
echo Script execution completed successfully.
