import requests
import json
from datetime import datetime, timezone
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ComEdAPI:
    """Client for fetching ComEd hourly pricing data.
    
    Prices returned are in cents/kWh.
    """
    
    BASE_URL = "https://hourlypricing.comed.com/api"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ComEd-Price-Monitor/1.0'
        })
    
    def get_current_hourly_price(self) -> Optional[Dict]:
        """Fetch the latest 5-minute price. Falls back to current hour average."""
        # Use 5-minute feed first for real-time accuracy
        result = self._fetch_endpoint("5minutefeed")
        if result:
            return result
        
        # Fall back to current hour average
        result = self._fetch_endpoint("currenthouraverage")
        if result:
            return result
        
        logger.error("All ComEd API endpoints failed")
        return None
    
    def get_5min_prices(self) -> Optional[List[Dict]]:
        """Fetch all 5-minute prices for today."""
        try:
            url = f"{self.BASE_URL}?type=5minutefeed"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if not data:
                return None
            return [self._parse_entry(entry, url) for entry in data]
        except Exception as e:
            logger.error(f"Error fetching 5-minute feed: {e}")
            return None
    
    def _fetch_endpoint(self, feed_type: str) -> Optional[Dict]:
        """Fetch and parse a single ComEd API endpoint."""
        url = f"{self.BASE_URL}?type={feed_type}"
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            text = response.text.strip()
            if "Servlet Feed" in text:
                logger.warning(f"Endpoint {feed_type} returned maintenance message")
                return None
            
            data = response.json()
            if not data:
                return None
            
            # API returns a JSON array; take the first (most recent) entry
            latest = data[0] if isinstance(data, list) else data
            result = self._parse_entry(latest, url)
            
            if result and result['price'] is not None:
                logger.info(f"Got price {result['price']} cents/kWh from {feed_type}")
                return result
            
            return None
            
        except json.JSONDecodeError:
            logger.warning(f"Non-JSON response from {feed_type}")
            return None
        except requests.RequestException as e:
            logger.warning(f"Request failed for {feed_type}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {feed_type}: {e}")
            return None
    
    def _parse_entry(self, entry: Dict, source: str) -> Optional[Dict]:
        """Parse a single {millisUTC, price} entry from the API."""
        try:
            price = float(entry['price'])
            millis = int(entry['millisUTC'])
            dt = datetime.fromtimestamp(millis / 1000, tz=timezone.utc)
            
            return {
                'price': price,
                'timestamp': dt.astimezone().strftime('%Y-%m-%d %H:%M:%S %Z'),
                'source': source,
                'raw_data': entry
            }
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Failed to parse entry {entry}: {e}")
            return None
