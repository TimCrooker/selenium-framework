from pydantic import BaseModel
from typing import Optional


class Bot(BaseModel):
    name: str
    script: str  # Path to the bot script
    schedule: Optional[str] = None  # Cron expression or interval


class BotInDB(Bot):
    id: str
    status: str


class Run(BaseModel):
    bot_id: str
    status: str
    start_time: str
    container_id: Optional[str] = None
    end_time: Optional[str] = None
    logs: Optional[str] = ''
    run_id: Optional[str] = None
