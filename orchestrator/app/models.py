from pydantic import BaseModel
from typing import Optional


class RegisterBot(BaseModel):
    name: str
    script: str
    schedule: Optional[str] = None

class BotInDB(BaseModel):
    id: str
    name: str
    script: str
    schedule: Optional[str] = None

class Run(BaseModel):
    bot_id: str
    status: str
    agent_id: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None

class Agent(BaseModel):
		agent_id: str
		status: str
		last_heartbeat: Optional[str] = None
		resources: dict
		public_url: Optional[str] = None

class RunLog(BaseModel):
		run_id: str
		timestamp: str
		message: str
		screenshot: Optional[str] = None
		payload: Optional[dict] = None