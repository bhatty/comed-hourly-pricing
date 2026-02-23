import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import os
from datetime import datetime
from slack_alerts import SlackAlertManager

logger = logging.getLogger(__name__)

class AlertSystem:
    """Handles sending alerts via different channels"""
    
    def __init__(self, config: dict):
        self.config = config
        self.email_enabled = config.get('EMAIL_ENABLED', 'false').lower() == 'true'
        
        if self.email_enabled:
            self.smtp_server = config.get('SMTP_SERVER')
            self.smtp_port = int(config.get('SMTP_PORT', 587))
            self.email_username = config.get('EMAIL_USERNAME')
            self.email_password = config.get('EMAIL_PASSWORD')
            self.email_to = config.get('EMAIL_TO')
        
        # Initialize Slack alert manager
        self.slack_manager = SlackAlertManager(config)
    
    def send_alert(self, alert_data: dict) -> bool:
        """Send alert through all enabled channels"""
        success = True
        
        # Always send to console
        self._send_console_alert(alert_data)
        
        # Send email if enabled
        if self.email_enabled:
            email_success = self._send_email_alert(alert_data)
            success = success and email_success
        
        # Send Slack alert if enabled
        slack_success = self.slack_manager.send_alert(alert_data)
        success = success and slack_success
        
        return success
    
    def _send_console_alert(self, alert_data: dict):
        """Send alert to console"""
        message = alert_data.get('message', 'Price alert triggered')
        price = alert_data.get('price', 'N/A')
        timestamp = alert_data.get('timestamp', 'N/A')
        
        print("\n" + "="*60)
        print(f"🚨 COMED PRICE ALERT 🚨")
        print(f"Time: {timestamp}")
        print(f"Price: {price}¢/kWh")
        print(f"Message: {message}")
        print("="*60 + "\n")
        
        # Also log it
        logger.warning(f"PRICE ALERT: {message}")
    
    def _send_email_alert(self, alert_data: dict) -> bool:
        """Send alert via email"""
        if not all([self.smtp_server, self.email_username, self.email_password, self.email_to]):
            logger.error("Email configuration incomplete")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_username
            msg['To'] = self.email_to
            msg['Subject'] = f"ComEd Price Alert: {alert_data.get('price', 'N/A')}¢/kWh"
            
            # Create email body
            body = self._create_email_body(alert_data)
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_username, self.email_password)
                server.send_message(msg)
            
            logger.info(f"Email alert sent to {self.email_to}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False
    
    def _create_email_body(self, alert_data: dict) -> str:
        """Create HTML email body"""
        price = alert_data.get('price', 'N/A')
        timestamp = alert_data.get('timestamp', 'N/A')
        alert_type = alert_data.get('alert_type', 'unknown')
        threshold = alert_data.get('threshold', 0)
        
        if alert_type == 'negative_price':
            color = '#ff0000'
            emoji = '🚨'
            title = 'NEGATIVE PRICE ALERT'
        else:
            color = '#ff9900'
            emoji = '📉'
            title = 'LOW PRICE ALERT'
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: {color}; margin: 0;">{emoji} {title}</h1>
                    <p style="color: #666; margin: 10px 0 0 0;">ComEd Hourly Pricing Monitor</p>
                </div>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin: 0 0 15px 0; color: #333;">Alert Details</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px; font-weight: bold; color: #555;">Current Price:</td>
                            <td style="padding: 8px; color: {color}; font-size: 18px; font-weight: bold;">{price}¢/kWh</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; font-weight: bold; color: #555;">Alert Threshold:</td>
                            <td style="padding: 8px;">{threshold}¢/kWh</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; font-weight: bold; color: #555;">Time:</td>
                            <td style="padding: 8px;">{timestamp}</td>
                        </tr>
                    </table>
                </div>
                
                <div style="margin: 20px 0;">
                    <h3 style="margin: 0 0 10px 0; color: #333;">What this means:</h3>
                    <p style="margin: 0; color: #666; line-height: 1.6;">
                        {self._get_price_explanation(alert_type, price)}
                    </p>
                </div>
                
                <div style="margin: 30px 0; padding: 20px; background-color: #e8f5e8; border-radius: 8px;">
                    <h3 style="margin: 0 0 10px 0; color: #2d5a2d;">💡 Recommendations:</h3>
                    <ul style="margin: 0; padding-left: 20px; color: #2d5a2d;">
                        {self._get_recommendations(alert_type)}
                    </ul>
                </div>
                
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                    <p style="color: #999; font-size: 12px; margin: 0;">
                        This alert was generated by ComEd Price Monitor on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_body
    
    def _get_price_explanation(self, alert_type: str, price: float) -> str:
        """Get explanation for the price alert"""
        if alert_type == 'negative_price':
            return f"The electricity price is currently negative at {price}¢/kWh. This means you're essentially being paid to use electricity! This is extremely rare and usually happens during periods of very high renewable energy generation and low demand."
        else:
            return f"The electricity price is currently very low at {price}¢/kWh, which is below your alert threshold. This is a great opportunity to use electricity-intensive appliances."
    
    def _get_recommendations(self, alert_type: str) -> str:
        """Get recommendations based on alert type"""
        if alert_type == 'negative_price':
            recommendations = [
                "Charge electric vehicles immediately",
                "Run dishwasher, laundry, and other appliances",
                "Adjust thermostat to heat/cool more than usual",
                "Consider storing thermal energy (hot water, etc.)",
                "This is essentially free electricity - use it!"
            ]
        else:
            recommendations = [
                "Good time to run dishwasher and laundry",
                "Consider charging electric vehicles",
                "Use electricity-intensive appliances if needed",
                "Defer non-urgent tasks to normal price periods if possible"
            ]
        
        return '\n'.join([f"<li>{rec}</li>" for rec in recommendations])
