import os
import json
import logging
from datetime import datetime
from monitor import PriceMonitor
from alerts import AlertSystem
from main import load_config

# Configure logging for Lambda (logs to CloudWatch)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    AWS Lambda handler for ComEd Price Monitor.
    Runs a single price check and sends alerts if necessary.
    """
    logger.info(f"ComEd Price Monitor Lambda triggered at {datetime.now().isoformat()}")

    try:
        # Load configuration from environment variables
        # Note: In Lambda, these are set in the function configuration
        config = load_config()

        # Initialize components
        monitor = PriceMonitor(price_threshold=config['PRICE_THRESHOLD'])
        alert_system = AlertSystem(config)

        # Run a single check
        result = monitor.fetch_and_check()

        if result['status'] == 'error':
            logger.error(f"Error checking price: {result['message']}")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'message': 'Error checking ComEd prices',
                    'error': result['message']
                })
            }

        logger.info(f"Price check successful: {result['price']}¢/kWh")

        # If an alert was triggered, it will be handled inside monitor.fetch_and_check()
        # but actually we should call alert_system.send_alert manually if result contains alert_data
        # because fetch_and_check just identifies if an alert is needed.
        if result.get('alert_data'):
            logger.info("Alert triggered! Sending notifications...")
            alert_system.send_alert(result['alert_data'])

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Price check completed successfully',
                'price': result['price'],
                'timestamp': result['timestamp'],
                'status': result['status'],
                'alert_triggered': bool(result.get('alert_data'))
            })
        }

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Internal server error',
                'error': str(e)
            })
        }
