from pymongo import MongoClient
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/")
client = MongoClient(MONGO_URI)
db = client['synthetic_monitoring']
bots_collection = db['bots']
runs_collection = db['runs']
