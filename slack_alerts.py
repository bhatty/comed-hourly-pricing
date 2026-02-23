import logging
import json
import requests
from typing import Optional, Dict
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)

class SlackAlertManager:
    """Handles sending alerts to Slack"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.enabled = config.get('SLACK_ENABLED', 'false').lower() == 'true'
        self.bot_token = config.get('SLACK_BOT_TOKEN')
        self.channel = config.get('SLACK_CHANNEL', '#comed-price-alerts')
        self.webhook_url = config.get('SLACK_WEBHOOK_URL')
        
        # Initialize Slack client if bot token is provided
        self.slack_client = None
        if self.enabled and self.bot_token:
            try:
                self.slack_client = WebClient(token=self.bot_token)
                logger.info("Slack client initialized with bot token")
            except Exception as e:
                logger.error(f"Failed to initialize Slack client: {e}")
                self.enabled = False
    
    def send_alert(self, alert_data: Dict) -> bool:
        """Send alert to Slack"""
        if not self.enabled:
            logger.debug("Slack alerts disabled")
            return True
        
        success = True
        
        # Try webhook first (simpler, no bot permissions needed)
        if self.webhook_url and self.webhook_url != "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK":
            webhook_success = self._send_webhook_alert(alert_data)
            success = success and webhook_success
        
        # Try bot token as backup or primary
        elif self.slack_client:
            bot_success = self._send_bot_alert(alert_data)
            success = success and bot_success
        else:
            logger.warning("No valid Slack configuration found")
            return False
        
        return success
    
    def _send_webhook_alert(self, alert_data: Dict) -> bool:
        """Send alert using Slack webhook"""
        try:
            payload = self._create_webhook_payload(alert_data)
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Slack webhook alert sent successfully")
                return True
            else:
                logger.error(f"Slack webhook failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Slack webhook alert: {e}")
            return False
    
    def _send_bot_alert(self, alert_data: Dict) -> bool:
        """Send alert using Slack bot token"""
        try:
            blocks = self._create_slack_blocks(alert_data)
            
            response = self.slack_client.chat_postMessage(
                channel=self.channel,
                blocks=blocks,
                text=f"ComEd Price Alert: {alert_data.get('price', 'N/A')}¢/kWh"
            )
            
            logger.info(f"Slack bot alert sent to {self.channel}")
            return True
            
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return False
        except Exception as e:
            logger.error(f"Failed to send Slack bot alert: {e}")
            return False
    
    def _create_webhook_payload(self, alert_data: Dict) -> Dict:
        """Create webhook payload for Slack"""
        price = alert_data.get('price', 'N/A')
        timestamp = alert_data.get('timestamp', 'N/A')
        alert_type = alert_data.get('alert_type', 'unknown')
        
        if alert_type == 'negative_price':
            emoji = '🚨'
            color = 'danger'
            title = 'NEGATIVE PRICE ALERT'
        else:
            emoji = '📉'
            color = 'warning'
            title = 'LOW PRICE ALERT'
        
        payload = {
            "username": "ComEd Price Monitor",
            "icon_emoji": ":zap:",
            "channel": self.channel,
            "attachments": [
                {
                    "color": color,
                    "title": f"{emoji} {title}",
                    "title_link": "https://hourlypricing.comed.com/live-prices/",
                    "fields": [
                        {
                            "title": "Current Price",
                            "value": f"{price}¢/kWh",
                            "short": True
                        },
                        {
                            "title": "Time",
                            "value": timestamp,
                            "short": True
                        },
                        {
                            "title": "What this means",
                            "value": self._get_price_explanation(alert_type, price),
                            "short": False
                        },
                        {
                            "title": "💡 Recommendations",
                            "value": self._get_recommendations_text(alert_type),
                            "short": False
                        }
                    ],
                    "footer": "ComEd Price Monitor",
                    "ts": self._get_timestamp()
                }
            ]
        }
        
        return payload
    
    def _create_slack_blocks(self, alert_data: Dict) -> list:
        """Create Slack blocks for bot message"""
        price = alert_data.get('price', 'N/A')
        timestamp = alert_data.get('timestamp', 'N/A')
        alert_type = alert_data.get('alert_type', 'unknown')
        
        if alert_type == 'negative_price':
            emoji = '🚨'
            color = '#ff0000'
            title = 'NEGATIVE PRICE ALERT'
        else:
            emoji = '📉'
            color = '#ff9900'
            title = 'LOW PRICE ALERT'
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {title}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Current Price:*\n{price}¢/kWh"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Time:*\n{timestamp}"
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*What this means:*\n{self._get_price_explanation(alert_type, price)}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*💡 Recommendations:*\n{self._get_recommendations_text(alert_type)}"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"<https://hourlypricing.comed.com/live-prices/|View Live Prices> • ComEd Price Monitor"
                    }
                ]
            }
        ]
        
        return blocks
    
    def _get_price_explanation(self, alert_type: str, price: float) -> str:
        """Get explanation for the price alert"""
        if alert_type == 'negative_price':
            return f"The electricity price is currently negative at {price}¢/kWh. This means you're essentially being paid to use electricity! This is extremely rare and usually happens during periods of very high renewable energy generation and low demand."
        else:
            return f"The electricity price is currently very low at {price}¢/kWh, which is below your alert threshold. This is a great opportunity to use electricity-intensive appliances."
    
    def _get_recommendations_text(self, alert_type: str) -> str:
        """Get recommendations as formatted text"""
        if alert_type == 'negative_price':
            recommendations = [
                "🔋 Charge electric vehicles immediately",
                "🧺 Run dishwasher, laundry, and other appliances",
                "🌡️ Adjust thermostat to heat/cool more than usual",
                "♨️ Consider storing thermal energy (hot water, etc.)",
                "💡 This is essentially free electricity - use it!"
            ]
        else:
            recommendations = [
                "🧺 Good time to run dishwasher and laundry",
                "🔋 Consider charging electric vehicles",
                "⚡ Use electricity-intensive appliances if needed",
                "⏰ Defer non-urgent tasks to normal price periods if possible"
            ]
        
        return '\n'.join(recommendations)
    
    def _get_timestamp(self) -> int:
        """Get Unix timestamp"""
        from datetime import datetime
        return int(datetime.now().timestamp())
    
    def test_connection(self) -> bool:
        """Test Slack connection"""
        if not self.enabled:
            logger.info("Slack alerts disabled")
            return True
        
        # Test webhook
        if self.webhook_url and self.webhook_url != "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK":
            try:
                test_payload = {
                    "text": "🧪 ComEd Price Monitor - Test Connection",
                    "username": "ComEd Price Monitor",
                    "icon_emoji": ":zap:"
                }
                
                response = requests.post(self.webhook_url, json=test_payload, timeout=10)
                
                if response.status_code == 200:
                    logger.info("Slack webhook test successful")
                    return True
                else:
                    logger.error(f"Slack webhook test failed: {response.status_code}")
                    return False
                    
            except Exception as e:
                logger.error(f"Slack webhook test error: {e}")
                return False
        
        # Test bot token
        elif self.slack_client:
            try:
                response = self.slack_client.auth_test()
                logger.info(f"Slack bot test successful - connected as {response['user']}")
                return True
            except SlackApiError as e:
                logger.error(f"Slack bot test failed: {e.response['error']}")
                return False
        else:
            logger.warning("No valid Slack configuration for testing")
            return False
