from pymongo import MongoClient
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client['bot_orchestration']

agents_collection = db['agents']
bots_collection = db['bots']
runs_collection = db['runs']
run_logs_collection = db['run_logs']

agents_collection.create_index("agent_id", unique=True)
runs_collection.create_index("bot_id", unique=False)