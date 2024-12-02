from datetime import datetime
from enum import Enum
from typing import Any, Optional
from bson import ObjectId
from pydantic import BaseModel, Field, validator

from app.utils.cron import validate_cron_expression


class ObjectIdStr(str):
    @classmethod
    def __get_validators__(cls) -> Any:
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> str:
        if not ObjectId.is_valid(v):
            raise ValueError(f"Invalid ObjectId: {v}")
        return str(v)

class MongoModel(BaseModel):
    id: ObjectIdStr = Field(alias="_id")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: str
        }
        allow_population_by_field_name = True

class RunStatus(str, Enum):
    QUEUED = "queued"
    SCHEDULED = "scheduled"
    STARTING = "starting"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class AgentStatus(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    STOPPED = "stopped"
    OFFLINE = "offline"

class BotInDB(BaseModel):
    id: str
    name: str
    script: str
    schedule: Optional[str] = None

# RUN MODELS

class RunBase(BaseModel):
    bot_id: str
    status: RunStatus
    agent_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class CreateRun(RunBase):
    status: RunStatus = RunStatus.QUEUED

class UpdateRun(BaseModel):
    status: Optional[RunStatus] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    agent_id: Optional[str] = None

class RunStatusUpdate(BaseModel):
    run_id: ObjectIdStr
    status: RunStatus

class SerializedRun(MongoModel, RunBase):
    pass

# RUN LOG MODELS

class RunLogBase(BaseModel):
    run_id: ObjectIdStr
    level: LogLevel
    message: str
    payload: Optional[dict[str, Any]] = None

class CreateRunLog(RunLogBase):
    pass

class SerializedRunLog(MongoModel, RunLogBase):
    timestamp: datetime

# RUN EVENT MODELS
class RunEventBase(BaseModel):
    run_id: ObjectIdStr
    event_type: str
    message: str
    payload: Optional[dict[str, Any]] = None
    screenshot: Optional[str] = None

class CreateRunEvent(RunEventBase):
    pass

class SerializedRunEvent(MongoModel, RunEventBase):
    timestamp: datetime

# AGENT MODELS

class AgentBase(BaseModel):
    agent_id: str
    status: AgentStatus
    resources: dict[str, Any]
    public_url: Optional[str] = None
    last_heartbeat: Optional[datetime] = None

class CreateAgent(AgentBase):
    pass

class UpdateAgent(BaseModel):
    status: Optional[AgentStatus] = None
    resources: Optional[dict[str, Any]] = None
    public_url: Optional[str] = None
    last_heartbeat: Optional[datetime] = None

class SerializedAgent(MongoModel, AgentBase):
    pass

class AgentStatusUpdate(BaseModel):
    status: AgentStatus

class AgentHeartbeatEvent(BaseModel):
    agent_id: str

class AgentLogEvent(BaseModel):
    agent_id: str
    log: str

# AGENT LOG MODELS

# BOT MODELS

class BotBase(BaseModel):
    name: str
    script: str
    schedule: Optional[str] = None
    created_at: Optional[datetime] = None

    @validator('schedule')
    def validate_schedule(cls, v: Any) -> Any:
        if v and not validate_cron_expression(v):
            raise ValueError("Invalid CRON expression")
        return v

class CreateBot(BotBase):
    pass

class UpdateBot(BaseModel):
    name: Optional[str] = None
    script: Optional[str] = None
    schedule: Optional[str] = None

    @validator('schedule')
    def validate_schedule(cls, v: Any) -> Any:
        if v and not validate_cron_expression(v):
            raise ValueError("Invalid CRON expression")
        return v

class SerializedBot(MongoModel, BotBase):
    pass