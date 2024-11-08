import asyncio
import requests

from .bot_executor import BotExecutor
from .utils.communication import send_agent_log, send_post
from .utils.config import AGENT_URL, HEARTBEAT_INTERVAL, ORCHESTRATOR_URL, AGENT_ID

executor = BotExecutor()

async def execute_bot(bot_id, bot_script, run_id):
    """Start executing a bot."""
    await executor.run_bot_script(bot_id, bot_script, run_id)

async def stop_bot(bot_id):
    """Stop a running bot."""
    await executor.stop_bot(bot_id)

async def register_agent():
    """Register the agent with the orchestrator."""
    payload = {
        "agent_id": AGENT_ID,
        "status": "available",
        "resources": {
            "cpu": "normal",  # Update this based on the agent's actual capabilities
            "memory": "normal"  # Update this based on the agent's actual capabilities
        },
        "public_url": AGENT_URL
    }
    try:
        await send_post(f"{ORCHESTRATOR_URL}/agents/register", payload)
        print(f"Agent {AGENT_ID} successfully registered.")
    except requests.RequestException as e:
        print(f"Error registering agent: {e}")

async def send_heartbeat():
    """Send periodic heartbeat to the orchestrator."""
    while True:
        try:
            await send_post(f"{ORCHESTRATOR_URL}/agents/{AGENT_ID}/heartbeat", {})
            await send_agent_log(f"Hearbeat test: {AGENT_ID}")
            print(f"Heartbeat sent from agent {AGENT_ID}")
        except Exception as e:
            print(f"Failed to send heartbeat: {e}")
        await asyncio.sleep(HEARTBEAT_INTERVAL)
