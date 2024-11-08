import os

# Base URLs and configurations
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")
AGENT_ID = os.getenv("AGENT_ID", "agent-1")
AGENT_URL = os.getenv("AGENT_URL", "http://localhost:9000")

# Directory configurations
BOTS_DIRECTORY = os.getenv("BOTS_DIRECTORY", "/app/bots")

HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", 10))  # in seconds