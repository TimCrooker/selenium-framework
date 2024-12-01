import asyncio

from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel

from ..models import Agent
from ..utils.socket_manager import sio
from ..utils.config import HEARTBEAT_INTERVAL
from ..database import agents_collection

def serialize_agent(agent: Agent):
    return {
      "id": str(agent["_id"]),
      "agent_id": agent["agent_id"],
      "status": agent["status"],
      "resources": agent["resources"],
      "public_url": agent.get("public_url"),
      "last_heartbeat": agent.get("last_heartbeat").isoformat() if agent.get("last_heartbeat") else None
    }

async def register_agent(agent_data):
    try:
        agents_collection.update_one(
            {"agent_id": agent_data["agent_id"]},
            {"$set": {
              "status": agent_data["status"],
              "resources": agent_data["resources"],
              "public_url": agent_data["public_url"],
              "last_heartbeat": datetime.now()}
            },
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Error registering agent: {e}")
        return False

async def agent_heartbeat(agent_id):
    agents_collection.update_one(
        {"agent_id": agent_id},
        {"$set": {"last_heartbeat": datetime.now(), "status": "available"}}
    )
    await emit_agent_update(agent_id)

async def update_agent_status(agent_id, status):
    agents_collection.update_one(
        {"agent_id": agent_id},
        {"$set": {"status": status}}
    )
    await emit_agent_update(agent_id)

async def get_agent_url(agent_id):
    agent = agents_collection.find_one({"agent_id": agent_id})
    return agent.get("public_url") if agent else None

async def find_available_agent():
    """Assign an available agent to a bot."""
    agent = agents_collection.find_one({"last_heartbeat": {"$gt": datetime.now() - timedelta(seconds=HEARTBEAT_INTERVAL * 2)}})
    return agent

async def monitor_agents():
    while True:
        now = datetime.now()
        cutoff = now - timedelta(seconds=2 * HEARTBEAT_INTERVAL)
        agents_collection.update_many(
            {"last_heartbeat": {"$lt": cutoff}},
            {"$set": {"status": "stopped"}}
        )
        await asyncio.sleep(HEARTBEAT_INTERVAL)

# INCOMING EVENTS
class AgentLogEvent(BaseModel):
    agent_id: str
    log: str

@sio.on('agent_log')
async def agent_log(sid, data: AgentLogEvent):
    agent_id = data.get('agent_id')
    log_message = data.get('log')
    print(f"AGENT Log received for agent {agent_id}: {log_message}")
    await emit_agent_log(agent_id, log_message)

# UI EVNET HANDLERS
class AgentUpdateEvent(BaseModel):
    agent_id: str
    status: Optional[str] = None
    last_heartbeat: Optional[str] = None
    resources: Optional[dict] = None
    public_url: Optional[str] = None

async def emit_agent_update(agent_id: str):
    agent = agents_collection.find_one({"agent_id": agent_id})
    if not agent:
        print(f"Agent {agent_id} not found")
        return

    serialized_agent = serialize_agent(agent)
    print(f"EMITTING AGENT UPDATE")
    await sio.emit('agent_updated', serialized_agent, namespace='/ui')

async def emit_agent_log(agent_id: str, log_message: str):
    print(f"EMITTING AGENT LOG")
    await sio.emit('agent_log_created', {"agent_id": agent_id, "log": log_message}, namespace='/ui')