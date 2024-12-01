import asyncio
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
import psutil

from .utils.navigation import click_element, input_text, wait_for_element
from app.utils.socket_manager import sio

class BaseBot(ABC):
    def __init__(self, run_id: str, socket_url: str, orchestrator_url: str):
        self.run_id = run_id
        self.start_time = time.time()
        self.session_data = []

        self.sio = socketio.Client(
            reconnection=True,
            reconnection_attempts=5,
            reconnection_delay=5,
            logger=False,
            engineio_logger=False
        )
        self.socket_url = socket_url
        self.sio.connect(socket_url)

        self.logger = None
        self.orchestrator_url = orchestrator_url
        self.driver = self._get_driver()

        signal.signal(signal.SIGTERM, self.handle_termination)
        signal.signal(signal.SIGINT, self.handle_termination)

    def _get_driver(self):
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')

        driver = webdriver.Chrome(options=options)
        return driver

    @abstractmethod
    async def run(self):
        pass

    def _get_stack_trace(self):
        import traceback
        return traceback.format_exc()

    async def handle_termination(self, *args):
        await self.teardown()
        sys.exit(0)

    async def handle_error(self, error):
        payload = {
            "error": str(error),
            "stack_trace": self._get_stack_trace()
        }
        screenshot_base64 = await self.capture_screenshot()
        await self.send_run_event("error", screenshot=screenshot_base64, payload=payload)
        await self.teardown()

    async def teardown(self):
        if self.driver:
            self.driver.quit()
        if self.sio.connected:
            self.sio.disconnect()

    async def send_run_event(self, message, screenshot=None, payload=None):
        if not self.sio.connected:
            self.sio.connect(self.socket_url)

        event_data = {
            "run_id": self.run_id,
            "message": message,
            "screenshot": screenshot,
            "payload": payload,
        }
        sio.emit('bot:run_event', event_data, namespace='/bot')

    async def send_run_log(self, log_message):
        await self.send_run_event(
            message=log_message
        )

    async def capture_screenshot(self):
        try:
            screenshot = self.driver.get_screenshot_as_png()
            return base64.b64encode(screenshot).decode('utf-8')
        except Exception as e:
            await self.send_run_log(f"Failed to capture screenshot: {str(e)}")
            return None

    async def capture_system_metrics(self):
        try:
            process = psutil.Process(os.getpid())
            cpu_usage = psutil.cpu_percent()
            memory_info = process.memory_info()
            memory_usage = memory_info.rss / (1024 * 1024)
            return {'cpu_usage': cpu_usage, 'memory_usage_mb': memory_usage}
        except Exception as e:
            await self.send_run_log(f"Failed to capture system metrics: {str(e)}")
            return None

    async def wait_and_click(self, locator, timeout=10):
        result = await click_element(self.driver, locator, timeout)
        if not result:
            await self.send_run_log(f"Failed to click element: {locator}")

    async def wait_and_input_text(self, locator, text, timeout=10):
        result = await input_text(self.driver, locator, text, timeout)
        if not result:
            await self.send_run_log(f"Failed to input text into element: {locator}")

    async def wait_for_element_presence(self, locator, timeout=10):
        element = await wait_for_element(self.driver, locator, timeout)
        if not element:
            await self.send_run_log(f"Element not found: {locator}")
        return element

    async def capture_state(self):
        screenshot_base64 = await self.capture_screenshot()
        await self.send_run_event("Captured current state", screenshot=screenshot_base64)
