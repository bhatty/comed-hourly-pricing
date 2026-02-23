# Windows Deployment Guide

## Option 1: Windows Service (Recommended for always-on)

The Windows Service runs continuously in the background and starts automatically with Windows.

### Prerequisites
- Windows 10/11 or Windows Server
- Python 3.7+ installed
- Administrator privileges

### Installation

1. **Download and extract** the comed-price-monitor folder
2. **Open Command Prompt as Administrator** (right-click → "Run as administrator")
3. **Navigate to the project directory:**
   ```cmd
   cd C:\path\to\comed-price-monitor
   ```
4. **Run the installer:**
   ```cmd
   deploy\install_windows_service.bat
   ```

### Managing the Service

```cmd
# Start the service
python deploy\windows_service.py start

# Check status
python deploy\windows_service.py status

# Stop the service
python deploy\windows_service.py stop

# Remove the service
python deploy\windows_service.py remove
```

Or use Windows Services GUI:
1. Press `Win + R`, type `services.msc`
2. Find "ComEd Price Monitor"
3. Right-click to start/stop

### Logs
- Service logs: `comed_service.log`
- Monitor logs: `comed_monitor.log`

---

## Option 2: Windows Task Scheduler (Simpler)

Runs the monitor at regular intervals using Windows Task Scheduler.

### Prerequisites
- Windows 10/11
- Python 3.7+ installed
- PowerShell (included with Windows)

### Installation

1. **Extract the comed-price-monitor folder**
2. **Open PowerShell as Administrator**
3. **Navigate to the project directory:**
   ```powershell
   cd C:\path\to\comed-price-monitor
   ```
4. **Run the setup script:**
   ```powershell
   .\deploy\setup_windows_task.ps1
   ```

### Managing the Task

```powershell
# Check task status
Get-ScheduledTask -TaskName "ComEdPriceMonitor"

# Start immediately
Start-ScheduledTask -TaskName "ComEdPriceMonitor"

# Stop the task
Stop-ScheduledTask -TaskName "ComEdPriceMonitor"

# Remove the task
Unregister-ScheduledTask -TaskName "ComEdPriceMonitor"
```

### Customizing the Task

To change the check interval (default: 10 minutes):
```powershell
.\deploy\setup_windows_task.ps1 -IntervalMinutes 30
```

---

## Option 3: Simple Batch File (Manual)

For testing or occasional use.

### Create a batch file

Create `run_monitor.bat`:
```batch
@echo off
cd /d "%~dp0"
python main.py --monitor
pause
```

Double-click to run, or add to Windows Startup folder.

---

## Configuration

Edit `config.env` before deployment:

```env
# Slack alerts (recommended for mobile notifications)
SLACK_ENABLED=true
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK

# Email alerts (optional)
EMAIL_ENABLED=true
SMTP_SERVER=smtp.gmail.com
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_TO=your_email@gmail.com

# Monitoring settings
CHECK_INTERVAL_MINUTES=10
PRICE_THRESHOLD=0.0
```

---

## Mobile Notifications

### Slack (Recommended)
1. Install Slack app on your phone
2. Enable notifications for your alert channel
3. You'll get instant push notifications for price alerts

### Email
Configure email settings in `config.env` to receive alerts via email.

---

## Troubleshooting

### Service won't start
- Check Event Viewer → Windows Logs → Application
- Verify Python and pywin32 are installed correctly
- Ensure config.env exists and is properly formatted

### Task not running
- Open Task Scheduler and check the task status
- Review the task history for errors
- Verify the Python path in the task action

### No alerts
- Check `comed_monitor.log` for errors
- Verify Slack webhook URL is correct
- Test with: `python main.py --test-slack`

### Permissions issues
- Run installation scripts as Administrator
- Ensure the service/task has network access for API calls

---

## Firewall Settings

If your Windows firewall blocks the application:

1. Open Windows Defender Firewall
2. Go to "Allow an app or feature through Windows Defender Firewall"
3. Add exceptions for:
   - Python (python.exe)
   - Your network access for `hourlypricing.comed.com`

---

## Performance Impact

- **CPU usage**: Minimal (< 1% during checks)
- **Memory usage**: ~20-50MB
- **Network usage**: < 1MB per day
- **Disk usage**: Logs grow slowly (~1MB per week)

The monitor is very lightweight and won't impact system performance.
