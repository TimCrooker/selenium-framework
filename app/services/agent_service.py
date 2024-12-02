from datetime import datetime, timedelta
from typing import Any, Optional

from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder

from ..models import AgentLogEvent, AgentStatus, CreateAgent, SerializedAgent, UpdateAgent
from ..utils.socket_manager import sio
from ..utils.config import HEARTBEAT_INTERVAL
from ..database import agents_collection

def serialize_agent(agent: dict[str, Any]) -> SerializedAgent:
    return SerializedAgent(**agent)

async def create_agent(agent_data: CreateAgent) -> Optional[SerializedAgent]:
    try:
        payload = agent_data.dict()
        payload["last_heartbeat"] = datetime.now()
        await agents_collection.update_one(
            {"agent_id": agent_data.agent_id},
            {"$set": payload},
            upsert=True
        )
        agent = await agents_collection.find_one({"agent_id": agent_data.agent_id})

        if not agent:
            raise Exception("Error registering agent")

        serialized_agent = serialize_agent(agent)
        await emit_agent_update(serialized_agent)
        return serialized_agent
    except Exception as e:
        print(f"Error registering agent: {e}")
        return None

async def get_agent_by_id(agent_id: str) -> Optional[SerializedAgent]:
    agent = await agents_collection.find_one({"agent_id": agent_id})
    if agent:
        return serialize_agent(agent)
    return None

async def update_agent(agent_id: str, data: UpdateAgent) -> Optional[SerializedAgent]:
    try:
        payload = data.dict(exclude_unset=True)
        await agents_collection.update_one(
            {"agent_id": agent_id},
            {"$set": payload}
        )
        agent = await agents_collection.find_one({"agent_id": agent_id})
        if not agent:
            return None
        serialized_agent = serialize_agent(agent)
        await emit_agent_update(serialized_agent)
        return serialized_agent
    except Exception as e:
        print(f"Error updating agent {agent_id}: {e}")
        return None

async def list_agents() -> list[SerializedAgent]:
    try:
        agents_cursor = agents_collection.find()
        agents = await agents_cursor.to_list(length=None)
        return [serialize_agent(agent) for agent in agents]
    except Exception as e:
        print(f"Error listing agents: {e}")
        return []

async def list_available_agents() -> list[SerializedAgent]:
    try:
        agents_cursor = agents_collection.find({"status": AgentStatus.AVAILABLE.value})
        agents = await agents_cursor.to_list(length=None)
        return [serialize_agent(agent) for agent in agents]
    except Exception as e:
        print(f"Error listing available agents: {e}")
        return []

async def agent_heartbeat(agent_id: str, status: AgentStatus) -> Optional[SerializedAgent]:
    return await update_agent(agent_id, UpdateAgent(last_heartbeat=datetime.now(), status=status))


async def update_agent_status(agent_id: str, status: AgentStatus) -> Optional[SerializedAgent]:
    return await update_agent(agent_id, UpdateAgent(status=status.value))

async def find_available_agent() -> Optional[SerializedAgent]:
    try:
        cutoff = datetime.now() - timedelta(seconds=HEARTBEAT_INTERVAL * 2)
        agent = await agents_collection.find_one({
            "last_heartbeat": {"$gt": cutoff},
            "status": AgentStatus.AVAILABLE.value
        })
        if agent:
            return serialize_agent(agent)
        return None
    except Exception as e:
        print(f"Error finding available agent: {e}")
        return None

async def monitor_agents() -> None:
    try:
        now = datetime.now()
        cutoff = now - timedelta(seconds=5 * HEARTBEAT_INTERVAL)
        await agents_collection.update_many(
            {"last_heartbeat": {"$lt": cutoff}},
            {"$set": {"status": AgentStatus.OFFLINE.value}}
        )
        print(f"[Monitor] Checked agents at {now.isoformat()}")
    except Exception as e:
        print(f"Error monitoring agents: {e}")

async def create_agent_log(agent_id: str, log_message: str) -> None:
    await emit_agent_log(agent_id, log_message)


# EVENT HANDLERS

@sio.on('agent_log', namespace='/agent')
async def handle_agent_log(sid: str, data: dict[str, Any]) -> None:
    try:
        event = AgentLogEvent(**data)
        await create_agent_log(event.agent_id, event.log)
    except Exception as e:
        print(f"Invalid log data: {e}")

@sio.on('agent_heartbeat', namespace='/agent')
async def handle_agent_heartbeat(sid: str, data: dict[str, Any]) -> None:
    try:
        agent_id: Any = data.get('agent_id')
        status: Any = data.get('status')

        await agent_heartbeat(agent_id, status)
    except Exception as e:
        print(f"Invalid heartbeat data: {e}")

class AgentStatusUpdate(BaseModel):
    agent_id: str
    status: AgentStatus

@sio.on('agent_status_update', namespace='/agent')
async def handle_agent_status_update(sid: str, data: dict[str, Any]) -> None:
    try:
        event = AgentStatusUpdate(**data)
        await update_agent_status(event.agent_id, event.status)
    except Exception as e:
        print(f"Error handling agent status update: {e}")


# EVENT EMITTERS

async def emit_agent_update(agent: SerializedAgent) -> None:
    data = jsonable_encoder(agent)
    await sio.emit('agent_updated', data, namespace='/ui')

async def emit_agent_log(agent_id: str, log_message: str) -> None:
    data = jsonable_encoder({
        "agent_id": agent_id,
        "log": log_message,
        "timestamp": datetime.now()
    })
    await sio.emit('agent_log_created', data, namespace='/ui')
