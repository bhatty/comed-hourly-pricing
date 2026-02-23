import logging
import time
from datetime import datetime
from typing import Optional
from comed_api import ComEdAPI

logger = logging.getLogger(__name__)

class PriceMonitor:
    """Monitors ComEd hourly prices and alerts on negative prices"""
    
    def __init__(self, price_threshold: float = 0.0):
        self.api = ComEdAPI()
        self.price_threshold = price_threshold
        self.last_alert_time = None
        self.alert_cooldown_minutes = 30  # Prevent spam alerts
    
    def fetch_and_check(self) -> dict:
        """Fetch price once, return status dict with optional alert_data."""
        try:
            price_data = self.api.get_current_hourly_price()
            
            if not price_data or price_data.get('price') is None:
                return {'status': 'error', 'message': 'Failed to fetch price data'}
            
            price = price_data['price']
            timestamp = price_data['timestamp']
            
            logger.info(f"Current price: {price}¢/kWh at {timestamp}")
            
            status = 'negative' if price < 0 else 'low' if price <= self.price_threshold else 'normal'
            
            result = {
                'status': status,
                'price': price,
                'timestamp': timestamp,
                'threshold': self.price_threshold,
                'source': price_data.get('source'),
                'alert_data': None
            }
            
            # Check if price is below threshold (negative by default)
            if price <= self.price_threshold and self._should_send_alert():
                result['alert_data'] = {
                    'price': price,
                    'timestamp': timestamp,
                    'threshold': self.price_threshold,
                    'source': price_data.get('source'),
                    'alert_type': 'negative_price' if price < 0 else 'low_price',
                    'message': self._generate_alert_message(price, timestamp)
                }
                self.last_alert_time = datetime.now()
            elif price <= self.price_threshold:
                logger.info(f"Price {price}¢/kWh is below threshold but in cooldown period")
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking price: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _should_send_alert(self) -> bool:
        """Check if enough time has passed since last alert"""
        if self.last_alert_time is None:
            return True
            
        time_since_last = datetime.now() - self.last_alert_time
        return time_since_last.total_seconds() >= (self.alert_cooldown_minutes * 60)
    
    def _generate_alert_message(self, price: float, timestamp: str) -> str:
        """Generate alert message"""
        if price < 0:
            return f"🚨 NEGATIVE PRICE ALERT! ComEd price is {price}¢/kWh at {timestamp}. Time to use electricity!"
        else:
            return f"📉 LOW PRICE ALERT: ComEd price is {price}¢/kWh at {timestamp}. Good time to use electricity."
