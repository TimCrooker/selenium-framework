from datetime import datetime
from bson import ObjectId
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.run_service import create_run_event, serialize_run, serialize_run_log, update_run
from ..database import runs_collection, run_logs_collection

router = APIRouter()

@router.get("/")
def get_runs():
    """Retrieve all bot runs."""
    runs = list(runs_collection.find())
    return [serialize_run(run) for run in runs]

@router.get("/{run_id}")
async def get_run(run_id: str):
    """Retrieve logs for a specific run."""
    run = runs_collection.find_one({"_id": ObjectId(run_id)})
    if run:
        return serialize_run(run)
    raise HTTPException(status_code=404, detail="Run not found")

@router.get("/{run_id}/logs")
async def get_run_logs(run_id: str):
    """Retrieve logs for a specific run."""
    run = runs_collection.find_one({"_id": ObjectId(run_id)})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # fetch all run logs from database with this run_id
    logs = list(run_logs_collection.find({"run_id": run_id}))
    return [serialize_run_log(log) for log in logs]

class RunStatusUpdate(BaseModel):
    status: str

@router.post("/{run_id}/status")
async def update_run_status(run_id: str, status_update: RunStatusUpdate):
    """Update the status of a specific run."""
    run = runs_collection.find_one({"_id": ObjectId(run_id)})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    status = status_update.status

    if status == "running":
        await update_run(run_id, {"status": status, "start_time": datetime.now()})
        await create_run_event({
            "run_id": run_id,
            "timestamp": datetime.now(),
            "message": "Run started"
        })

    if status == "completed":
        await update_run(run_id, {"status": status, "end_time": datetime.now()})
        await create_run_event({
            "run_id": run_id,
            "timestamp": datetime.now(),
            "message": "Run completed"
        })

    if status == "error":
        await update_run(run_id, {"status": status, "end_time": datetime.now()})
        await create_run_event({
            "run_id": run_id,
            "timestamp": datetime.now(),
            "message": "Run failed"
        })

    await update_run(run_id, {"status": status})