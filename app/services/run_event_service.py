from datetime import datetime
from typing import Any

from fastapi.encoders import jsonable_encoder

from app.database import run_events_collection
from app.models import CreateRunEvent, SerializedRunEvent
from app.utils.socket_manager import sio

def serialize_run_event(run_event: dict[str, Any]) -> SerializedRunEvent:
    return SerializedRunEvent(**run_event)

async def create_run_event(data: CreateRunEvent) -> SerializedRunEvent:
    try:
        payload = data.dict()
        payload["timestamp"] = datetime.now()
        result = run_events_collection.insert_one(payload)
        event = run_events_collection.find_one({"_id": result.inserted_id})
        if not event:
            raise Exception("Error creating run event")

        serialized_run_event = serialize_run_event(event)
        await emit_run_event(serialized_run_event)
        return serialized_run_event
    except Exception as e:
        # Handle exception
        raise e

def list_run_events(run_id: str) -> list[SerializedRunEvent]:
    try:
        events = run_events_collection.find({"run_id": run_id})
        return [serialize_run_event(event) for event in events]
    except Exception as e:
        # Handle exception
        raise e

# EVENT HANDLERS

@sio.on("run_event", namespace='/agent')
async def handle_run_event(sid: str, data: dict[str, Any]) -> None:
    print(f"Received 'run_event' event from SID {sid}: {data}")
    try:
        event_data = CreateRunEvent(**data)
        await create_run_event(event_data)
    except Exception as e:
        print(f"Error handling run event: {e}")

# EVENT EMITTER

async def emit_run_event(run_event: SerializedRunEvent) -> None:
    print(f"Emitting 'run_event' event: {run_event}")
    data = jsonable_encoder(run_event)
    await sio.emit("run_event", data, namespace='/ui')