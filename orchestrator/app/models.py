from pydantic import BaseModel
from typing import Optional
from datetime import datetime


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
    agent_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class Agent(BaseModel):
		agent_id: str
		status: str
		last_heartbeat: Optional[datetime] = None
		resources: dict
		public_url: Optional[str] = None

class RunLog(BaseModel):
		run_id: str
		timestamp: datetime
		message: str
		screenshot: Optional[str] = None
		payload: Optional[dict] = None