import base64
import os
import requests
import sys
import time
import signal
from abc import ABC, abstractmethod
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import socketio

class BaseBot(ABC):
    def __init__(self, run_id, socket_url, orchestrator_url):
        self.run_id = run_id
        self.start_time = time.time()
        self.session_data = []

        # Setup Socket.IO client
        self.sio = socketio.Client()
        self.sio.connect(socket_url)

        # Setup the logger
        self.logger = None

        # Setup the API client for the orchestrator
        self.orchestrator_url = orchestrator_url

        # WebDriver setup
        self.driver = self._get_driver()

        # Handle termination signals
        signal.signal(signal.SIGTERM, self.handle_termination)
        signal.signal(signal.SIGINT, self.handle_termination)

    def _get_driver(self):
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')

        # Initialize the driver
        driver = webdriver.Chrome(options=options)
        return driver

    async def capture_screenshot(self):
        try:
            screenshot = self.driver.get_screenshot_as_png()

            return base64.b64encode(screenshot).decode('utf-8')
        except Exception as e:
            await self.send_run_log(f"Failed to capture screenshot: {str(e)}")
            return None

    # OUTGOING SOCKET.IO EVENTS

    async def send_run_event(self, message, screenshot=None, payload=None):
        event_data = {
            "run_id": self.run_id,
            "message": message,
            "screenshot": screenshot,
            "payload": payload,
        }
        await self.sio.emit('run_event', event_data)

    async def send_run_log(self, log_message):
        await self.send_run_event(message=log_message)

    def _get_stack_trace(self):
        import traceback
        return traceback.format_exc()

    def handle_termination(self, signum, frame):
        self.teardown()
        sys.exit(0)

    async def handle_error(self, error):
        payload = {
            "error": str(error),
            "stack_trace": self._get_stack_trace()
        }
        screenshot_base64 = self.capture_screenshot()

        await self.send_run_event("error", screenshot=screenshot_base64, payload=payload)

    @abstractmethod
    async def run(self):
        """Run method to be implemented by each bot"""
        pass

    async def teardown(self):
        elapsed_time = time.time() - self.start_time
        session_summary = {
"          payload": {
            'action': 'session_summary',
            'total_execution_time': elapsed_time,
            'status': 'completed'
          }
        }
        await self.send_run_event(session_summary)
        if self.driver:
            self.driver.quit()
        self.sio.disconnect()
