import os

ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")
AGENT_ID = os.getenv("AGENT_ID", "agent-1")
AGENT_URL = os.getenv("AGENT_URL", "http://localhost:9000")

HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", 10))