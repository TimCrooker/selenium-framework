from typing import Optional
from pydantic import BaseModel

class AgentRegistration(BaseModel):
    agent_id: str
    status: str
    resources: dict

class RunStatusUpdate(BaseModel):
    run_id: str
    status: str
    message: Optional[str] = None

class BotRunRequest(BaseModel):
    bot_id: str
    bot_script: str
    run_id: str