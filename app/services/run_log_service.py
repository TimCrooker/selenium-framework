from datetime import datetime
from pydantic import BaseModel
from app.database import run_logs_collection
from app.models import SerializedRunLog
from app.utils.socket_manager import sio

def serialize_run_log(run_log) -> SerializedRunLog:
    return {
        "id": str(run_log["_id"]),
        "run_id": run_log["run_id"],
        "timestamp": run_log["timestamp"].isoformat() if run_log.get("timestamp") else None,
        "message": run_log["message"],
        "screenshot": run_log.get("screenshot"),
        "payload": run_log.get("payload")
    }

class CreateRunLogEvent(BaseModel):
    run_id: str
    message: str
    screenshot: str = None
    payload: dict = None

async def create_run_event(data: CreateRunLogEvent):
    run_log = data.model_dump()
    run_log["timestamp"] = datetime.now()
    run_logs_collection.insert_one(run_log)

    await emit_run_event_created(run_log["_id"])

    return serialize_run_log(run_log)

async def emit_run_event_created(run_log_id):
    run_log = run_logs_collection.find_one({"_id": run_log_id})
    if not run_log:
        return

    serialized_run_log = serialize_run_log(run_log)
    await sio.emit("run_event_created", serialized_run_log, namespace='/ui')