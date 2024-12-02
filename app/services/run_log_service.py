from datetime import datetime
from typing import Any

from fastapi.encoders import jsonable_encoder

from app.database import run_logs_collection
from app.models import CreateRunLog, SerializedRunLog
from app.utils.socket_manager import sio

def serialize_run_log(run_log: dict[str, Any]) -> SerializedRunLog:
    return SerializedRunLog(**run_log)

async def create_run_log(data: CreateRunLog) -> SerializedRunLog:
    try:
        payload = data.dict()
        payload["timestamp"] = datetime.now()
        result = run_logs_collection.insert_one(payload)
        log = run_logs_collection.find_one({"_id": result.inserted_id})
        if not log:
            raise Exception("Error creating run log")

        serialized_run_log = serialize_run_log(log)
        await emit_run_log(serialized_run_log)
        return serialized_run_log
    except Exception as e:
        # Handle exception
        raise e

def list_run_logs(run_id: str) -> list[SerializedRunLog]:
    try:
        logs = run_logs_collection.find({"run_id": run_id})
        return [serialize_run_log(log) for log in logs]
    except Exception as e:
        # Handle exception
        raise e

# EVENT HANDLERS

@sio.on("run_log", namespace='/agent')
async def handle_run_log_event(sid: str, data: dict[str, Any]) -> None:
    try:
        log_data = CreateRunLog(**data)
        await create_run_log(log_data)
    except Exception as e:
        print(f"Error handling run log event: {e}")

# EVENT EMITTERS

async def emit_run_log(run_log: SerializedRunLog) -> None:
    data = jsonable_encoder(run_log)
    await sio.emit("run_log", data, namespace='/ui')