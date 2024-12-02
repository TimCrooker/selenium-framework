from datetime import datetime
from typing import Any

from bson import ObjectId
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder

from app.services.run_event_service import create_run_event

from ..database import runs_collection
from ..models import (CreateRun, CreateRunEvent, RunStatus, RunStatusUpdate, SerializedRun, UpdateRun)
from ..utils.socket_manager import sio


def serialize_run(run: dict[str, Any]) -> SerializedRun:
    return SerializedRun(**run)

async def create_run(data: CreateRun) -> SerializedRun:
    try:
        payload = data.dict()
        payload["start_time"] = payload.get("start_time") or datetime.now()
        result = runs_collection.insert_one(payload)
        run = runs_collection.find_one({"_id": result.inserted_id})
        if not run:
            raise Exception("Error creating run")

        serialized_run = serialize_run(run)
        await emit_run_created(serialized_run)
        return serialized_run
    except Exception as e:
        # Handle exception
        raise e

def get_run_by_id(run_id: str) -> SerializedRun:
    try:
        run = runs_collection.find_one({"_id": ObjectId(run_id)})
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")

        return serialize_run(run)
    except Exception as e:
        # Handle exception
        raise e

async def update_run(run_id: str, data: UpdateRun) -> SerializedRun:
    try:
        payload = data.dict(exclude_unset=True)
        runs_collection.update_one({"_id": ObjectId(run_id)}, {"$set": payload})
        run = runs_collection.find_one({"_id": ObjectId(run_id)})
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")

        serialized_run = serialize_run(run)
        await emit_run_updated(serialized_run)
        return serialized_run
    except Exception as e:
        # Handle exception
        raise e

def list_runs() -> list[SerializedRun]:
    runs = list(runs_collection.find())
    return [serialize_run(run) for run in runs]

async def queue_run(bot_id: str) -> SerializedRun:
    run = await create_run(CreateRun(bot_id=bot_id, status="queued"))

    return run

async def schedule_run(bot_id: str, start_time: datetime) -> SerializedRun:
    run = await create_run(CreateRun(
        bot_id=bot_id,
        status=RunStatus.SCHEDULED,
        start_time=start_time
    ))

    return run

async def update_run_status(run_id: str, status: RunStatus) -> SerializedRun:
    try:
        run = runs_collection.find_one({"_id": ObjectId(run_id)})
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")

        update_data = UpdateRun(status=status)
        return await update_run(run_id, update_data)
    except Exception as e:
        raise e

# EVENT HANDLERS

@sio.on('update_run_status', namespace='/agent')
async def handle_run_status_update(sid: str, data: dict[str, Any]) -> None:
    print(f"Received 'update_run_status' event from SID {sid}: {data}")
    try:
        status_update = RunStatusUpdate(**data)
        print(f"Handling run status update: {status_update}")
        await update_run_status(status_update.run_id, status_update.status)
    except Exception as e:
        print(f"Error handling run status update: {e}")

# EVENT EMITTERS

async def emit_run_created(run: SerializedRun) -> None:
    print(f"Emitting 'run_created' event: {run}")
    data = jsonable_encoder(run)
    await sio.emit('run_created', data, namespace='/ui')

async def emit_run_updated(run: SerializedRun) -> None:
    print(f"Emitting 'run_updated' event: {run}")
    data = jsonable_encoder(run)
    await sio.emit('run_updated', data, namespace='/ui')
