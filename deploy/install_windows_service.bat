@echo off
echo Installing ComEd Price Monitor as Windows Service...
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Please run this script as Administrator
    echo Right-click the script and select "Run as administrator"
    pause
    exit /b 1
)

REM Install Python dependencies
echo Installing Python dependencies...
pip install -r requirements.txt
pip install pywin32

REM Install the Windows service
echo Installing Windows service...
python deploy/windows_service.py install

if %errorLevel% neq 0 (
    echo ERROR: Failed to install service
    pause
    exit /b 1
)

echo.
echo Service installed successfully!
echo.
echo To start the service:
echo   python deploy/windows_service.py start
echo.
echo Or start it from Windows Services (services.msc)
echo.
echo To check status:
echo   python deploy/windows_service.py status
echo.
echo To stop the service:
echo   python deploy/windows_service.py stop
echo.
echo To remove the service:
echo   python deploy/windows_service.py remove
echo.
pause
