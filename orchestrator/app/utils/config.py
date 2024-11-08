import os

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "synthetic_monitoring")

# Orchestrator URL (used for agents to communicate back)
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")

# General application settings
DEBUG = os.getenv("DEBUG", "False").lower() in ['true', '1']

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", 10))