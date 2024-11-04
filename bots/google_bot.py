import sys
import os
import time
import argparse
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from bots.base_bot import BaseBot, measure_latency
import logging
from pymongo import MongoClient
from bson.objectid import ObjectId
import socketio

class GoogleBot(BaseBot):
    def __init__(self, run_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.run_id = run_id
        # MongoDB client setup
        self.client = MongoClient('mongodb://mongo:27017/')
        self.db = self.client['synthetic_monitoring']
        self.runs_collection = self.db['runs']
        self.bots_collection = self.db['bots']
        self.update_run_status('running')

        # Socket.IO client setup
        self.sio = socketio.Client()
        self.sio.connect('http://orchestrator:8000')

    def update_run_status(self, status):
        if self.run_id:
            self.runs_collection.update_one(
                {"run_id": self.run_id},
                {"$set": {"status": status}},
                upsert=True
            )
            self.bots_collection.update_one(
                {"script": "bots/google_bot.py"},
                {"$set": {"status": status}}
            )
            # Emit status update
            self.sio.emit('bot_status', {'bot_id': str(self.get_bot_id()), 'status': status})

    def get_bot_id(self):
        bot = self.bots_collection.find_one({"script": "bots/google_bot.py"})
        return bot['_id']

    def run(self):
        try:
            self.update_run_status('running')
            # Perform the bot's main functionality
            self.perform_searches()
            # If successful, update the status to 'completed'
            self.update_run_status('completed')
        except Exception as e:
            # Handle exceptions and update status to 'error'
            self.update_run_status('error')
            self.logger.error(f"An error occurred: {e}")
        finally:
            self.teardown()

    @measure_latency
    def perform_searches(self):
        search_terms = ['OpenAI', 'Python programming', 'Selenium WebDriver']
        for term in search_terms:
            self.search_term(term)
            time.sleep(2)  # Wait before the next search

    @measure_latency
    def search_term(self, term):
        self.driver.get('https://www.google.com')
        start_time = time.time()
        search_box = self.driver.find_element(By.NAME, 'q')
        search_box.clear()
        search_box.send_keys(term)
        search_box.send_keys(Keys.RETURN)

        # Wait for results to load
        time.sleep(2)

        # Verify that results are displayed
        results = self.driver.find_elements(By.CSS_SELECTOR, 'div.g')
        action_latency = time.time() - start_time
        if results:
            event_data = {
                'timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                'bot_name': self.__class__.__name__,
                'action': 'search_term',
                'search_term': term,
                'results_count': len(results),
                'latency': action_latency,
                'status': 'success'
            }
            self.log_event(event_data)
        else:
            error_message = f"No results found for '{term}'."
            raise Exception(error_message)

    def log_event(self, event_data):
        super().log_event(event_data)
        # Emit log event
        self.sio.emit('bot_log', {'run_id': self.run_id, 'event_data': event_data})

    def teardown(self):
        super().teardown()
        self.sio.disconnect()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run GoogleBot.')
    parser.add_argument('--run_id', help='Run ID for tracking in the orchestrator')
    args = parser.parse_args()

    bot = GoogleBot(run_id=args.run_id)
    bot.run()
