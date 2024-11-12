import requests
import asyncio

from .config import ORCHESTRATOR_URL, AGENT_ID
from .socket_manager import sio

# API Communication

async def send_post(url, data):
    """Send a POST request to the given URL with retry logic."""
    attempts = 0
    while attempts < 5:
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error sending POST to {url}: {e}. Attempt {attempts + 1}/5")
            attempts += 1
            await asyncio.sleep(5)  # Add a delay before retrying
    return None

async def update_agent_status(status):
    payload = {
        "status": status,
    }
    await send_post(f"{ORCHESTRATOR_URL}/agents/{AGENT_ID}/status", payload)

async def update_run_status(run_id, status):
    payload = {
        "status": status,
    }
    await send_post(f"{ORCHESTRATOR_URL}/runs/{run_id}/status", payload)

async def register_agent():
    payload = {
        "agent_id": AGENT_ID,
        "status": "available",
        "resources": {"cpu": "normal", "memory": "normal"},
    }
    await send_post(f"{ORCHESTRATOR_URL}/agents/register", payload)

# OUTGOING SOCKET.IO EVENTS FROM AGENT

async def send_run_log(run_id, log_message):
    if sio.connected:
        await send_run_event(run_id, message=log_message)
    else:
        print("Socket.IO not connected. Log not sent.")

async def send_run_event(run_id, message, screenshot=None, payload=None):
    if sio.connected:
        event_data = {
            "run_id": run_id,
            "message": message,
            "screenshot": screenshot,
            "payload": payload,
        }
        sio.emit('run_event', event_data)
    else:
        print("Socket.IO not connected. Event not sent.")

async def send_agent_log(log_message):
    if sio.connected:
        sio.emit('agent_log', {'agent_id': AGENT_ID, 'log': log_message})
        print(f"Agent log update sent: {log_message}")
    else:
        print("Socket.IO not connected. Agent log update not sent.")