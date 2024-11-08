from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.agent_service import agent_heartbeat, register_agent, serialize_agent, update_agent_status
from app.database import agents_collection

router = APIRouter()

class AgentRegistration(BaseModel):
    agent_id: str
    status: str
    resources: dict
    public_url: str

class AgentStatusUpdate(BaseModel):
    status: str

@router.get("/")
async def list_agents():
    """List all registered agents."""
    agents = list(agents_collection.find())
    serialized_agents = [serialize_agent(agent) for agent in agents]
    return {"agents": serialized_agents}

@router.post("/register")
async def register(agent: AgentRegistration):
    """Register a new agent."""
    print(f"Registering agent: {agent.dict()}")
    success = await register_agent(agent.dict())
    if success:
        return {"status": "Agent registered", "agent_id": agent.agent_id}
    raise HTTPException(status_code=500, detail="Agent registration failed")

@router.get("/available")
async def available_agents():
    """Retrieve all available agents and return them serialized."""
    agents = list(agents_collection.find({"status": "available"}))

    serialized_agents = [serialize_agent(agent) for agent in agents]

    return {"available_agents": serialized_agents}

@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    """Retrieve a single agent by ID."""
    agent = agents_collection.find_one({"agent_id": agent_id})
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return serialize_agent(agent)

@router.post("/{agent_id}/heartbeat")
async def heartbeat(agent_id: str):
    """Receive a heartbeat from an agent."""
    await agent_heartbeat(agent_id)
    return {"status": "Heartbeat received"}

@router.post("/{agent_id}/status")
async def update_agent_status_post(agent_id: str, status_update: AgentStatusUpdate):
    agent = agents_collection.find_one({"agent_id": agent_id})
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Update the agent's status in the agents collection
    await update_agent_status(agent_id, status_update.status)

    return {"status": "Agent status updated", "agent_id": agent_id}