import asyncio

from datetime import datetime, timedelta
from typing import Any, NoReturn, Optional

from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder

from ..models import AgentLogEvent, AgentStatus, CreateAgent, SerializedAgent, UpdateAgent
from ..utils.socket_manager import sio
from ..utils.config import HEARTBEAT_INTERVAL
from ..database import agents_collection
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def serialize_agent(agent: dict[str, Any]) -> SerializedAgent:
    return SerializedAgent(**agent)

async def create_agent(agent_data: CreateAgent) -> Optional[SerializedAgent]:
    try:
        payload = agent_data.dict()
        payload["last_heartbeat"] = datetime.now()
        agents_collection.update_one(
            {"agent_id": agent_data.agent_id},
            {"$set": payload},
            upsert=True
        )
        agent = agents_collection.find_one({"agent_id": agent_data.agent_id})

        if not agent:
            raise Exception("Error registering agent")

        serialized_agent = serialize_agent(agent)
        await emit_agent_update(serialized_agent)
        return serialized_agent
    except Exception as e:
        print(f"Error registering agent: {e}")
        return None

def get_agent_by_id(agent_id: str) -> Optional[SerializedAgent]:
    agent = agents_collection.find_one({"agent_id": agent_id})
    if agent:
        return serialize_agent(agent)
    return None

async def update_agent(agent_id: str, data: UpdateAgent) -> Optional[SerializedAgent]:
    try:
        payload = data.dict(exclude_unset=True)
        agents_collection.update_one(
            {"agent_id": agent_id},
            {"$set": payload}
        )
        agent = agents_collection.find_one({"agent_id": agent_id})
        if not agent:
            return None
        serialized_agent = serialize_agent(agent)
        await emit_agent_update(serialized_agent)
        return serialized_agent
    except Exception as e:
        print(f"Error updating agent {agent_id}: {e}")
        return None

def list_agents() -> list[SerializedAgent]:
    try:
        agents = list(agents_collection.find())
        return [serialize_agent(agent) for agent in agents]
    except Exception as e:
        print(f"Error listing agents: {e}")
        return []

def list_available_agents() -> list[SerializedAgent]:
    try:
        agents = list(agents_collection.find({"status": AgentStatus.AVAILABLE.value}))
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
        agent = agents_collection.find_one({
            "last_heartbeat": {"$gt": cutoff},
            "status": AgentStatus.AVAILABLE.value
        })
        if agent:
            return serialize_agent(agent)
        return None
    except Exception as e:
        print(f"Error finding available agent: {e}")
        return None

async def monitor_agents() -> NoReturn:
    while True:
        try:
            now = datetime.now()
            cutoff = now - timedelta(seconds=2 * HEARTBEAT_INTERVAL)
            agents_collection.update_many(
                {"last_heartbeat": {"$lt": cutoff}},
                {"$set": {"status": AgentStatus.OFFLINE.value}}
            )
        except Exception as e:
            print(f"Error monitoring agents: {e}")
        await asyncio.sleep(HEARTBEAT_INTERVAL)

async def create_agent_log(agent_id: str, log_message: str) -> None:
    await emit_agent_log(agent_id, log_message)


# EVENT HANDLERS

@sio.on('agent_log', namespace='/agent')
async def handle_agent_log(sid: str, data: dict[str, Any]) -> None:
    print(f"Received 'agent_log' event from SID {sid}: {data}")
    try:
        event = AgentLogEvent(**data)
        await create_agent_log(event.agent_id, event.log)
    except Exception as e:
        print(f"Invalid log data: {e}")

@sio.on('agent_heartbeat', namespace='/agent')
async def handle_agent_heartbeat(sid: str, data: dict[str, Any]) -> None:
    print(f"Received 'agent_heartbeat' event from SID {sid}: {data}")
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
    print(f"Received 'agent_status_update' event from SID {sid}: {data}")
    try:
        event = AgentStatusUpdate(**data)
        await update_agent_status(event.agent_id, event.status)
    except Exception as e:
        print(f"Error handling agent status update: {e}")


# EVENT EMITTERS

async def emit_agent_update(agent: SerializedAgent) -> None:
    print(f"Emitting 'agent_updated' event: {agent}")
    data = jsonable_encoder(agent)
    await sio.emit('agent_updated', data, namespace='/ui')

async def emit_agent_log(agent_id: str, log_message: str) -> None:
    print(f"Emitting 'agent_log_created' event for agent {agent_id}: {log_message}")
    data = jsonable_encoder({
        "agent_id": agent_id,
        "log": log_message,
        "timestamp": datetime.now()
    })
    await sio.emit('agent_log_created', data, namespace='/ui')
