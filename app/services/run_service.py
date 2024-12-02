from datetime import datetime, timedelta
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
        result = await runs_collection.insert_one(payload)
        run = await runs_collection.find_one({"_id": result.inserted_id})
        if not run:
            raise Exception("Error creating run")

        serialized_run = serialize_run(run)
        await emit_run_created(serialized_run)
        return serialized_run
    except Exception as e:
        # Handle exception
        raise e

async def get_run_by_id(run_id: str) -> SerializedRun:
    try:
        run = await runs_collection.find_one({"_id": ObjectId(run_id)})
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")

        return serialize_run(run)
    except Exception as e:
        # Handle exception
        raise e

async def update_run(run_id: str, data: UpdateRun) -> SerializedRun:
    try:
        payload = data.dict(exclude_unset=True)
        await runs_collection.update_one({"_id": ObjectId(run_id)}, {"$set": payload})
        run = await runs_collection.find_one({"_id": ObjectId(run_id)})
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")

        serialized_run = serialize_run(run)
        await emit_run_updated(serialized_run)
        return serialized_run
    except Exception as e:
        # Handle exception
        raise e

async def list_runs() -> list[SerializedRun]:
    runs_cursor = runs_collection.find()
    runs = await runs_cursor.to_list(length=None)
    return [serialize_run(run) for run in runs]

async def list_runs_by_agent(agent_id: str) -> list[SerializedRun]:
    runs_cursor = runs_collection.find({"agent_id": agent_id})
    runs = await runs_cursor.to_list(length=None)
    return [serialize_run(run) for run in runs]

async def list_runs_by_bot(bot_id: str) -> list[SerializedRun]:
    runs_cursor = runs_collection.find({"bot_id": bot_id})
    runs = await runs_cursor.to_list(length=None)
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
        run = await runs_collection.find_one({"_id": ObjectId(run_id)})
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")

        update_data = UpdateRun(status=status)

        if status == RunStatus.RUNNING:
            await create_run_event(CreateRunEvent(
                run_id=run_id,
                event_type="info",
                message="Run has started"
            ))
        elif status in [RunStatus.COMPLETED, RunStatus.ERROR]:
            update_data.end_time = datetime.now()

        return await update_run(run_id, update_data)
    except Exception as e:
        raise e

async def cleanup_stuck_runs() -> None:
    print("Cleaning up stuck runs...")
    try:
        cutoff_time = datetime.now() - timedelta(hours=1)
        stuck_runs_cursor = runs_collection.find({
            "status": {"$in": [RunStatus.STARTING, RunStatus.RUNNING]},
            "start_time": {"$lt": cutoff_time}
        })
        stuck_runs = await stuck_runs_cursor.to_list(length=None)
        print(f"Found {len(stuck_runs)} stuck runs")
        for run in stuck_runs:
            await update_run_status(str(run["_id"]), RunStatus.ERROR)
    except Exception as e:
        print(f"Error cleaning up stuck runs: {e}")

# EVENT HANDLERS

@sio.on('update_run_status', namespace='/agent')
async def handle_run_status_update(sid: str, data: dict[str, Any]) -> None:
    try:
        status_update = RunStatusUpdate(**data)
        await update_run_status(status_update.run_id, status_update.status)
    except Exception as e:
        print(f"Error handling run status update: {e}")

# EVENT EMITTERS

async def emit_run_created(run: SerializedRun) -> None:
    data = jsonable_encoder(run)
    await sio.emit('run_created', data, namespace='/ui')

async def emit_run_updated(run: SerializedRun) -> None:
    data = jsonable_encoder(run)
    await sio.emit('run_updated', data, namespace='/ui')