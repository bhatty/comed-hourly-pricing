#!/usr/bin/env python3
"""
Windows Service wrapper for ComEd Price Monitor
Install with: python windows_service.py install
Start with: python windows_service.py start
Stop with: python windows_service.py stop
Remove with: python windows_service.py remove
"""

import sys
import os
import time
import logging
import servicemanager
import win32service
import win32serviceutil
import win32event

# Add script directory to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from main import load_config, setup_logging
from monitor import PriceMonitor
from alerts import AlertSystem

class ComEdPriceMonitorService(win32serviceutil.ServiceFramework):
    """Windows Service for ComEd Price Monitor"""
    
    _svc_name_ = "ComEdPriceMonitor"
    _svc_display_name_ = "ComEd Price Monitor"
    _svc_description_ = "Monitors ComEd electricity prices and sends alerts for negative pricing"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.is_alive = True
    
    def SvcStop(self):
        """Stop the service"""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_alive = False
        logging.info("Service stopping...")
    
    def SvcDoRun(self):
        """Main service loop"""
        try:
            # Setup logging to Windows Event Log and file
            log_path = os.path.join(SCRIPT_DIR, 'comed_service.log')
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_path),
                    logging.StreamHandler()
                ]
            )
            
            logging.info("ComEd Price Monitor service starting")
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, '')
            )
            
            # Load configuration
            config = load_config()
            
            # Initialize components
            monitor = PriceMonitor(price_threshold=config['PRICE_THRESHOLD'])
            alert_system = AlertSystem(config)
            
            interval_seconds = config['CHECK_INTERVAL_MINUTES'] * 60
            
            logging.info(f"Service started - checking every {config['CHECK_INTERVAL_MINUTES']} minutes")
            
            # Main monitoring loop
            while self.is_alive:
                try:
                    result = monitor.fetch_and_check()
                    
                    if result['status'] == 'error':
                        logging.error(f"Error checking price: {result['message']}")
                    else:
                        logging.info(f"Price: {result['price']}¢/kWh at {result['timestamp']} - Status: {result['status']}")
                        
                        if result.get('alert_data'):
                            logging.warning("ALERT TRIGGERED!")
                            alert_system.send_alert(result['alert_data'])
                    
                    # Wait for next check or stop signal
                    if win32event.WaitForSingleObject(self.hWaitStop, interval_seconds) == win32event.WAIT_OBJECT_0:
                        break
                        
                except Exception as e:
                    logging.error(f"Error in monitoring loop: {e}")
                    time.sleep(60)  # Wait 1 minute before retrying
            
            logging.info("Service stopped")
            
        except Exception as e:
            logging.error(f"Service failed to start: {e}")
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_ERROR_TYPE,
                servicemanager.PYS_SERVICE_STOPPED,
                (self._svc_name_, str(e))
            )

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(ComEdPriceMonitorService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(ComEdPriceMonitorService)
