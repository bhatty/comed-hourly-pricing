# ComEd Price Monitor

A Python tool that monitors ComEd hourly electricity pricing and sends alerts when prices are negative or below a specified threshold. This helps you take advantage of times when electricity is essentially free or when you're being paid to use it!

## Features

- 🚀 **Real-time monitoring** of ComEd hourly pricing
- 🚨 **Alerts for negative prices** (when you're paid to use electricity)
- 📧 **Email notifications** with detailed explanations and recommendations
- 💬 **Slack notifications** to keep your team informed
- ⏰ **Configurable check intervals** and price thresholds
- 📊 **Price status reporting** with detailed information
- 📝 **Comprehensive logging** for troubleshooting

## How It Works

ComEd's Hourly Pricing program allows customers to pay electricity at the hourly market price. Sometimes, due to high renewable energy generation and low demand, prices can become negative - meaning you get paid to use electricity!

This tool:
1. Fetches current pricing data from ComEd's API
2. Monitors for prices below your threshold (default: $0.00 for negative prices)
3. Sends alerts via console, email, and/or Slack
4. Provides recommendations on when to use electricity-intensive appliances

## Installation

1. Clone or download this project
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Copy `config.env` and update the settings:

```bash
# Email configuration (optional)
EMAIL_ENABLED=false
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_TO=your_email@gmail.com

# Slack configuration (optional)
SLACK_ENABLED=false
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_CHANNEL=#comed-price-alerts
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# Monitoring settings
CHECK_INTERVAL_MINUTES=60
PRICE_THRESHOLD=0.0
```

### Email Setup (Optional)

For Gmail:
1. Enable 2-factor authentication
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Use the App Password in `EMAIL_PASSWORD`

### Slack Setup (Optional)

You have two options for Slack integration:

#### Option 1: Webhook URL (Easiest)
1. Create a Slack app: https://api.slack.com/apps
2. Enable "Incoming Webhooks"
3. Create a webhook URL for your desired channel
4. Copy the webhook URL to `SLACK_WEBHOOK_URL`
5. Set `SLACK_ENABLED=true`

#### Option 2: Bot Token (More Features)
1. Create a Slack app: https://api.slack.com/apps
2. Add "Bot Token Scopes": `chat:write`, `channels:read`
3. Install the app to your workspace
4. Copy the bot token (starts with `xoxb-`) to `SLACK_BOT_TOKEN`
5. Create a channel (e.g., `#comed-price-alerts`)
6. Invite the bot to the channel
7. Set `SLACK_ENABLED=true`

## Usage

### Single Price Check
```bash
python main.py --check
```

### Continuous Monitoring
```bash
python main.py --monitor
```

### Test Configuration
```bash
python main.py --test-slack    # Test Slack connection
python main.py --test-email    # Test email configuration
```

### Custom Settings
```bash
# Check every 30 minutes
python main.py --monitor --interval 30

# Alert when price drops below $0.05/MWh
python main.py --monitor --threshold 0.05

# Verbose logging
python main.py --monitor --log-level DEBUG
```

## Alert Types

### 🚨 Negative Price Alert
When price < $0.00/MWh - You're being paid to use electricity!

**Recommendations:**
- Charge electric vehicles immediately
- Run dishwasher, laundry, and other appliances
- Adjust thermostat to heat/cool more than usual
- Store thermal energy (hot water, etc.)

### 📉 Low Price Alert  
When price ≤ your threshold (e.g., $0.05/MWh)

**Recommendations:**
- Good time to run dishwasher and laundry
- Consider charging electric vehicles
- Use electricity-intensive appliances if needed

## Output Examples

### Normal Operation
```
🔌 ComEd Price Monitor
📧 Email alerts: Disabled
� Slack alerts: Enabled
�💰 Alert threshold: $0.0/MWh
⏰ Check interval: 60 minutes

🔍 Checking ComEd prices at 2026-02-23 10:17:00
💰 Current price: $25.4/MWh
📊 Status: normal
✅ No alerts triggered
```

### Alert Triggered
```
🚨 COMED PRICE ALERT 🚨
Time: 2026-02-23 02:30:00
Price: $-5.2/MWh
Message: 🚨 NEGATIVE PRICE ALERT! ComEd price is $-5.2/MWh at 2026-02-23 02:30:00. Time to use electricity!
============================================================
```

### Slack Alert Example
The tool sends rich Slack messages with:
- 🚨 Alert type and current price
- 📊 Detailed price information
- 💡 Actionable recommendations
- 🔗 Direct link to live prices

## Troubleshooting

### Common Issues

1. **"Servlet Feed" error**: ComEd API may be experiencing issues. The tool will retry and log errors.

2. **Email not sending**: Check your email configuration, especially:
   - App Password for Gmail (not regular password)
   - SMTP settings and port
   - Firewall blocking SMTP

3. **Slack not working**: 
   - Verify webhook URL or bot token
   - Ensure bot is invited to the channel
   - Check bot has required permissions
   - Use `--test-slack` to verify connection

4. **No price data**: The tool tries multiple API endpoints. Check the log file `comed_monitor.log` for details.

### Logs

Check `comed_monitor.log` for detailed information:
```bash
tail -f comed_monitor.log
```

### Testing

Test your configuration before running monitoring:
```bash
python main.py --test-slack
python main.py --test-email
```

## API Endpoints

The tool tries multiple ComEd API endpoints:
- `https://hourlypricing.comed.com/api?type=5min&id=1`
- `https://hourlypricing.comed.com/api?type=custhour&id=1`
- `https://hourlypricing.comed.com/api?type=dayrt&id=1`

## Contributing

Feel free to submit issues and enhancement requests!

## License

MIT License - feel free to use and modify.

## Disclaimer

This tool is not affiliated with ComEd. Price data is provided "as is" and may be subject to API changes or outages. Always verify critical pricing information through official ComEd channels.
