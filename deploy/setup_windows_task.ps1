# PowerShell script to set up Windows Task Scheduler for ComEd Price Monitor
# Run as: .\setup_windows_task.ps1

param(
    [string]$PythonPath = "python",
    [int]$IntervalMinutes = 10
)

Write-Host "Setting up ComEd Price Monitor as Windows Scheduled Task..." -ForegroundColor Green

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$MainScript = Join-Path $ScriptDir "main.py"
$LogPath = Join-Path $ScriptDir "comed_task.log"

# Check if main.py exists
if (-not (Test-Path $MainScript)) {
    Write-Host "ERROR: main.py not found at $MainScript" -ForegroundColor Red
    exit 1
}

# Remove existing task if it exists
Write-Host "Removing existing task (if any)..."
Unregister-ScheduledTask -TaskName "ComEdPriceMonitor" -ErrorAction SilentlyContinue

# Create the scheduled task
$Action = New-ScheduledTaskAction -Execute $PythonPath -Argument "-m main --monitor" -WorkingDirectory $ScriptDir
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes)
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Days 1)
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Write-Host "Creating scheduled task to run every $IntervalMinutes minutes..."
Register-ScheduledTask -TaskName "ComEdPriceMonitor" -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description "ComEd Price Monitor - alerts for negative electricity prices"

if ($?) {
    Write-Host "SUCCESS: Scheduled task created!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task details:" -ForegroundColor Yellow
    Get-ScheduledTask -TaskName "ComEdPriceMonitor" | Select-Object TaskName, State, Description
    Write-Host ""
    Write-Host "To run immediately:" -ForegroundColor Yellow
    Write-Host "  Start-ScheduledTask -TaskName 'ComEdPriceMonitor'"
    Write-Host ""
    Write-Host "To stop the task:" -ForegroundColor Yellow
    Write-Host "  Stop-ScheduledTask -TaskName 'ComEdPriceMonitor'"
    Write-Host ""
    Write-Host "To remove the task:" -ForegroundColor Yellow
    Write-Host "  Unregister-ScheduledTask -TaskName 'ComEdPriceMonitor'"
    Write-Host ""
    Write-Host "Logs will be written to: $LogPath" -ForegroundColor Cyan
} else {
    Write-Host "ERROR: Failed to create scheduled task" -ForegroundColor Red
    exit 1
}

Write-Host "Setup complete!" -ForegroundColor Green
