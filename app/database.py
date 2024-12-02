from pymongo import AsyncMongoClient
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = AsyncMongoClient(MONGO_URI)
db = client['bot_orchestration']

agents_collection = db['agents']
bots_collection = db['bots']
runs_collection = db['runs']
run_logs_collection = db['run_logs']
run_events_collection = db['run_events']