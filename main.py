#!/usr/bin/env python3
"""
ComEd Price Monitor
Monitors ComEd hourly pricing and alerts when prices are negative
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitor import PriceMonitor
from alerts import AlertSystem

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def setup_logging(log_level: str = 'INFO'):
    """Setup logging configuration"""
    log_path = os.path.join(SCRIPT_DIR, 'comed_monitor.log')
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_config():
    """Load configuration from environment variables"""
    config_path = os.path.join(SCRIPT_DIR, 'config.env')
    load_dotenv(config_path)
    
    config = {
        'EMAIL_ENABLED': os.getenv('EMAIL_ENABLED', 'false'),
        'SMTP_SERVER': os.getenv('SMTP_SERVER'),
        'SMTP_PORT': os.getenv('SMTP_PORT', '587'),
        'EMAIL_USERNAME': os.getenv('EMAIL_USERNAME'),
        'EMAIL_PASSWORD': os.getenv('EMAIL_PASSWORD'),
        'EMAIL_TO': os.getenv('EMAIL_TO'),
        'SLACK_ENABLED': os.getenv('SLACK_ENABLED', 'false'),
        'SLACK_BOT_TOKEN': os.getenv('SLACK_BOT_TOKEN'),
        'SLACK_CHANNEL': os.getenv('SLACK_CHANNEL', '#comed-price-alerts'),
        'SLACK_WEBHOOK_URL': os.getenv('SLACK_WEBHOOK_URL'),
        'CHECK_INTERVAL_MINUTES': int(os.getenv('CHECK_INTERVAL_MINUTES', '60')),
        'PRICE_THRESHOLD': float(os.getenv('PRICE_THRESHOLD', '0.0'))
    }
    
    return config

def run_single_check(monitor: PriceMonitor, alert_system: AlertSystem):
    """Run a single price check"""
    print(f"\n🔍 Checking ComEd prices at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    result = monitor.fetch_and_check()
    
    if result['status'] == 'error':
        print(f"❌ Error: {result['message']}")
        return False
    
    print(f"💰 Current price: {result['price']}¢/kWh")
    print(f"🕐 As of: {result['timestamp']}")
    print(f"📊 Status: {result['status']}")
    
    if result.get('alert_data'):
        print(f"🚨 ALERT TRIGGERED!")
        alert_system.send_alert(result['alert_data'])
    else:
        print("✅ No alerts triggered")
    
    return True

def run_continuous_monitoring(monitor: PriceMonitor, alert_system: AlertSystem, interval_minutes: int):
    """Run continuous monitoring"""
    print(f"🚀 Starting continuous monitoring (checking every {interval_minutes} minutes)")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            run_single_check(monitor, alert_system)
            
            # Wait for next check
            print(f"⏰ Next check in {interval_minutes} minutes...")
            time.sleep(interval_minutes * 60)
            
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped by user")
    except Exception as e:
        logging.error(f"Unexpected error in monitoring loop: {e}")
        print(f"❌ Error: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='ComEd Price Monitor')
    parser.add_argument('--check', action='store_true', help='Run single price check')
    parser.add_argument('--monitor', action='store_true', help='Run continuous monitoring')
    parser.add_argument('--interval', type=int, help='Check interval in minutes (overrides config)')
    parser.add_argument('--test-slack', action='store_true', help='Test Slack connection')
    parser.add_argument('--test-email', action='store_true', help='Test email configuration')
    parser.add_argument('--threshold', type=float, help='Price threshold for alerts (overrides config)')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Load configuration
    config = load_config()
    
    # Override with command line arguments if provided
    if args.interval:
        config['CHECK_INTERVAL_MINUTES'] = args.interval
    if args.threshold:
        config['PRICE_THRESHOLD'] = args.threshold
    
    # Initialize components
    monitor = PriceMonitor(price_threshold=config['PRICE_THRESHOLD'])
    alert_system = AlertSystem(config)
    
    print("🔌 ComEd Price Monitor")
    print(f"📧 Email alerts: {'Enabled' if config['EMAIL_ENABLED'] == 'true' else 'Disabled'}")
    print(f"� Slack alerts: {'Enabled' if config['SLACK_ENABLED'] == 'true' else 'Disabled'}")
    print(f"💰 Alert threshold: {config['PRICE_THRESHOLD']}¢/kWh")
    print(f"⏰ Check interval: {config['CHECK_INTERVAL_MINUTES']} minutes")
    
    # Validate email configuration if enabled
    if config['EMAIL_ENABLED'] == 'true':
        required_email_fields = ['SMTP_SERVER', 'EMAIL_USERNAME', 'EMAIL_PASSWORD', 'EMAIL_TO']
        missing_fields = [field for field in required_email_fields if not config.get(field)]
        if missing_fields:
            print(f"⚠️  Warning: Email enabled but missing configuration: {', '.join(missing_fields)}")
            print("   Email alerts will not work until these are configured in config.env")
    
    # Validate Slack configuration if enabled
    if config['SLACK_ENABLED'] == 'true':
        slack_config_ok = True
        if not config.get('SLACK_WEBHOOK_URL') or config.get('SLACK_WEBHOOK_URL') == 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK':
            if not config.get('SLACK_BOT_TOKEN') or config.get('SLACK_BOT_TOKEN') == 'xoxb-your-bot-token':
                slack_config_ok = False
        
        if not slack_config_ok:
            print("⚠️  Warning: Slack enabled but missing valid webhook URL or bot token")
            print("   Slack alerts will not work until properly configured in config.env")
            print("   See README.md for Slack setup instructions")
    
    if args.check:
        # Run single check
        success = run_single_check(monitor, alert_system)
        sys.exit(0 if success else 1)
    elif args.monitor:
        # Run continuous monitoring
        run_continuous_monitoring(monitor, alert_system, config['CHECK_INTERVAL_MINUTES'])
    elif args.test_slack:
        # Test Slack connection
        print("🧪 Testing Slack connection...")
        success = alert_system.slack_manager.test_connection()
        if success:
            print("✅ Slack connection test successful!")
        else:
            print("❌ Slack connection test failed")
        sys.exit(0 if success else 1)
    elif args.test_email:
        # Test email configuration
        print("🧪 Testing email configuration...")
        # Create a test alert
        test_alert = {
            'price': -1.23,
            'timestamp': datetime.now().isoformat(),
            'alert_type': 'negative_price',
            'message': 'Test email from ComEd Price Monitor'
        }
        success = alert_system._send_email_alert(test_alert)
        if success:
            print("✅ Email test successful!")
        else:
            print("❌ Email test failed")
        sys.exit(0 if success else 1)
    else:
        # Default: show help and run single check
        print("\nUsage:")
        print("  python main.py --check          # Run single price check")
        print("  python main.py --monitor         # Run continuous monitoring")
        print("  python main.py --test-slack      # Test Slack connection")
        print("  python main.py --test-email      # Test email configuration")
        print("  python main.py --monitor --interval 30  # Check every 30 minutes")
        print("\nRunning single check by default...\n")
        run_single_check(monitor, alert_system)

if __name__ == '__main__':
    main()
