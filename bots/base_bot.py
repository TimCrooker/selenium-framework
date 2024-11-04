import signal
import sys
import time
import logging
import json
import os
from abc import ABC, abstractmethod
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

def measure_latency(func):
    """Decorator to measure the execution time of methods."""
    def wrapper(self, *args, **kwargs):
        start_time = time.time()
        result = func(self, *args, **kwargs)
        latency = time.time() - start_time
        event_data = {
            'timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            'bot_name': self.__class__.__name__,
            'action': func.__name__,
            'latency': latency,
            'status': 'success'
        }
        self.log_event(event_data)
        return result
    return wrapper

class BaseBot(ABC):
    """Abstract base class for bots."""
    def __init__(self, screenshot_dir='screenshots', log_dir='logs'):
        self.driver = self._get_driver()
        self.start_time = time.time()
        self.screenshot_dir = screenshot_dir
        self.log_dir = log_dir
        os.makedirs(self.screenshot_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session_data = []
        signal.signal(signal.SIGTERM, self.handle_termination)

    def handle_termination(self, signum, frame):
        self.logger.info("Termination signal received. Cleaning up...")
        self.teardown()
        sys.exit(0)

    def _get_driver(self):
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(options=options)
        return driver

    @abstractmethod
    def run(self):
        """Main method to run the bot."""
        pass

    def log_event(self, event_data):
        """Log events in structured JSON format."""
        self.session_data.append(event_data)
        self.logger.info(json.dumps(event_data))

    def handle_error(self, error):
        """Handle errors, capture screenshots, and log them in detail."""
        error_data = {
            'timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            'bot_name': self.__class__.__name__,
            'status': 'error',
            'error': str(error),
            'error_type': type(error).__name__,
            'stack_trace': self._get_stack_trace(),
        }
        # Capture browser console logs
        console_logs = self._get_browser_logs()
        if console_logs:
            error_data['browser_logs'] = console_logs

        # Capture screenshot
        screenshot_path = self.capture_screenshot()
        if screenshot_path:
            error_data['screenshot_path'] = screenshot_path

        self.log_event(error_data)
        self.logger.error(json.dumps(error_data))

    def capture_screenshot(self):
        """Capture a screenshot of the current browser window."""
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        screenshot_filename = f"{self.__class__.__name__}_{timestamp}.png"
        screenshot_path = os.path.join(self.screenshot_dir, screenshot_filename)
        try:
            self.driver.save_screenshot(screenshot_path)
            return screenshot_path
        except Exception as e:
            self.logger.error(f"Failed to save screenshot: {e}")
            return None

    def _get_stack_trace(self):
        """Retrieve the current stack trace."""
        import traceback
        return traceback.format_exc()

    def _get_browser_logs(self):
        """Retrieve browser console logs."""
        try:
            logs = self.driver.get_log('browser')
            return logs
        except Exception as e:
            self.logger.error(f"Failed to get browser logs: {e}")
            return None

    def teardown(self):
        """Clean up resources and save session data."""
        elapsed_time = time.time() - self.start_time
        session_summary = {
            'timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            'bot_name': self.__class__.__name__,
            'action': 'session_summary',
            'total_execution_time': elapsed_time,
            'status': 'completed'
        }
        self.log_event(session_summary)
        self.driver.quit()
        # Save session data to a log file
        self._save_session_log()

    def _save_session_log(self):
        """Save the session data to a JSON log file."""
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        log_filename = f"{self.__class__.__name__}_{timestamp}.json"
        log_path = os.path.join(self.log_dir, log_filename)
        try:
            with open(log_path, 'w') as f:
                json.dump(self.session_data, f, indent=4)
            self.logger.info(f"Session log saved to {log_path}")
        except Exception as e:
            self.logger.error(f"Failed to save session log: {e}")