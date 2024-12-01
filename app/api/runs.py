from datetime import datetime
from bson import ObjectId
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models import Run

from ..services.run_service import CreateRunLogEvent, UpdateRun, create_run_event, serialize_run, serialize_run_log, update_run
from ..database import runs_collection, run_logs_collection

router = APIRouter()

@router.get("/")
def get_runs():
    runs = list(runs_collection.find())
    return [serialize_run(run) for run in runs]

@router.get("/{run_id}")
async def get_run(run_id: str):
    run = runs_collection.find_one({"_id": ObjectId(run_id)})
    if run:
        return serialize_run(run)
    raise HTTPException(status_code=404, detail="Run not found")

@router.get("/{run_id}/logs")
async def get_run_logs(run_id: str):
    run = runs_collection.find_one({"_id": ObjectId(run_id)})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    logs = list(run_logs_collection.find({"run_id": run_id}))
    return [serialize_run_log(log) for log in logs]

class RunStatusUpdate(BaseModel):
    status: str

@router.post("/{run_id}/status")
async def update_run_status(run_id: str, status_update: RunStatusUpdate):
    run = runs_collection.find_one({"_id": ObjectId(run_id)})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    status = status_update.status
    timestamp = datetime.now()

    if status == "queued":
        await update_run(run_id, UpdateRun(status=status))

    elif status == "starting":
        await update_run(run_id, UpdateRun(
            status=status,
            start_time=timestamp
        ))

        await create_run_event(
            CreateRunLogEvent(
                run_id=run_id,
                message="Run started",
                payload={"start_time": timestamp.isoformat()}
            )
        )

    elif status == "completed":
        await update_run(run_id, UpdateRun(
            status=status,
            end_time=timestamp
        ))

        await create_run_event(
            CreateRunLogEvent(
                run_id=run_id,
                message="Run completed",
                payload={"end_time": timestamp.isoformat()}
            )
        )

    elif status == "error":
        await update_run(run_id, UpdateRun(
            status=status,
            end_time=timestamp
        ))

        await create_run_event(
            CreateRunLogEvent(
                run_id=run_id,
                message="Run failed",
                payload={"end_time": timestamp.isoformat()}
            )
        )

    else:
        await update_run(run_id, UpdateRun(status=status))