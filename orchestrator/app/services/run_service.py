from datetime import datetime
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel
from ..models import Run, RunLog
from ..database import runs_collection, run_logs_collection
from ..utils.socket_manager import sio

def serialize_run(run: Run):
    return {
        "id": str(run["_id"]),
        "bot_id": run["bot_id"],
        "agent_id": run.get("agent_id"),
        "status": run["status"],
        "start_time": run.get("start_time").isoformat() if run.get("start_time") else None,
        "end_time": run.get("end_time").isoformat() if run.get("end_time") else None
    }

def serialize_run_log(run_log):
    return {
        "id": str(run_log["_id"]),
        "run_id": run_log["run_id"],
        "timestamp": run_log["timestamp"].isoformat() if run_log.get("timestamp") else None,
        "message": run_log["message"],
        "screenshot": run_log.get("screenshot"),
        "payload": run_log.get("payload")
    }

async def create_run_entry(bot_id, status="starting", start_time=None):
    run = {
        "bot_id": bot_id,
        "status": status,
        "start_time": start_time if start_time else datetime.now()
    }
    runs_collection.insert_one(run)

    result = serialize_run(run)

    await emit_run_created(result.get('id'))

    return result

class UpdateRun(BaseModel):
    status: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    agent_id: Optional[str] = None

async def update_run(run_id, data: UpdateRun):
    payload = data.model_dump(exclude_none=True)

    runs_collection.update_one(
        {"_id": ObjectId(run_id)},
        {"$set": payload}
    )

    updated_run = serialize_run(runs_collection.find_one({"_id": ObjectId(run_id)}))

    await emit_run_updated(run_id)

    return updated_run

class CreateRunLogEvent(BaseModel):
    run_id: str
    message: str
    screenshot: Optional[str] = None
    payload: Optional[dict] = None

async def create_run_event(data: CreateRunLogEvent):
    run_log = data.model_dump()
    run_log["timestamp"] = datetime.now()
    run_logs_collection.insert_one(run_log)

    await emit_run_event_created(run_log["_id"])

    return serialize_run_log(run_log)

# INCOMING EVENTS
class RunEvent(BaseModel):
    run_id: str
    timestamp: str
    message: str
    screenshot: Optional[str] = None
    payload: Optional[dict] = None
@sio.on("run_event")
async def run_event(sid, data: RunEvent):
    await create_run_event(
        CreateRunLogEvent(
            run_id=data.get('run_id'),
            message=data.get('message'),
            screenshot=data.get('screenshot'),
            payload=data.get('payload')
        )
    )

# OUTGOING EVENTS
async def emit_run_event_created(run_log_id):
    run_log = run_logs_collection.find_one({"_id": ObjectId(run_log_id)})
    if not run_log:
        print(f"Run log {run_log_id} not found")
        return

    serialized_run_log = serialize_run_log(run_log)
    print(f"EMITTING RUN LOG CREATED")
    await sio.emit('run_event_created', serialized_run_log)

async def emit_run_created(run_id):
    run = runs_collection.find_one({"_id": ObjectId(run_id)})
    if not run:
        print(f"Run {run_id} not found")
        return

    serialized_run = serialize_run(run)
    print(f"EMITTING RUN CREATED")
    await sio.emit('run_created', serialized_run)

async def emit_run_updated(run_id):
    run = runs_collection.find_one({"_id": ObjectId(run_id)})
    if not run:
        print(f"Run {run_id} not found")
        return

    serialized_run = serialize_run(run)
    print(f"EMITTING RUN UPDATE")
    await sio.emit('run_updated', serialized_run)