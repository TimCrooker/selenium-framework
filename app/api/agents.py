from fastapi import APIRouter, HTTPException
from app.models import AgentStatus, AgentStatusUpdate, CreateAgent, SerializedAgent, SerializedRun
from app.services.agent_service import agent_heartbeat, create_agent, get_agent_by_id, list_agents, list_available_agents, update_agent_status
from app.services.run_service import list_runs_by_agent

router = APIRouter()

@router.get("/")
async def get_agents() -> list[SerializedAgent]:
    try:
        return list_agents()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting agents: {e}")

@router.post("/register")
async def register(agent: CreateAgent) -> SerializedAgent:
    print(agent)
    try:
        success = await create_agent(agent)
        if not success:
            raise HTTPException(status_code=400, detail="Agent registration failed")
        return success
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registering agent: {e}")

@router.get("/available")
async def available_agents() -> list[SerializedAgent]:
    try:
        return list_available_agents()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting available agents: {e}")

@router.get("/{agent_id}")
async def get_agent(agent_id: str) -> SerializedAgent:
    try:
        agent = get_agent_by_id(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting agent: {e}")

@router.get("/{agent_id}/runs")
async def get_agent_runs(agent_id: str) -> list[SerializedRun]:
    try:
        return list_runs_by_agent(agent_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting runs for agent {agent_id}: {e}")

@router.post("/{agent_id}/heartbeat")
async def heartbeat(agent_id: str) -> SerializedAgent:
    try:
        updatedAgent = await agent_heartbeat(agent_id, status=AgentStatus.AVAILABLE)
        if not updatedAgent:
            raise HTTPException(status_code=404, detail="Agent heartbeat failed")
        return updatedAgent
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error handling heartbeat: {e}")

@router.post("/{agent_id}/status")
async def update_agent_status_post(agent_id: str, status_update: AgentStatusUpdate) -> SerializedAgent:
    try:
        agent = await update_agent_status(agent_id, status_update.status)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating agent status: {e}")