from fastapi import APIRouter
from pydantic import BaseModel

from app.models import CreateRunEvent, CreateRunLog, ObjectIdStr, RunStatus, SerializedRun, SerializedRunEvent, SerializedRunLog
from app.services.run_event_service import create_run_event, list_run_events
from app.services.run_log_service import create_run_log, list_run_logs
from app.services.run_service import get_run_by_id, list_runs, update_run_status

router = APIRouter()

@router.get("/", response_model=list[SerializedRun])
def get_runs() -> list[SerializedRun]:
    try:
        return list_runs()
    except Exception as e:
        raise e

@router.get("/{run_id}")
async def get_run(run_id: str) -> SerializedRun:
    try:
        return get_run_by_id(run_id)
    except Exception as e:
        raise e

@router.get("/{run_id}/logs")
async def get_run_logs(run_id: str) -> list[SerializedRunLog]:
    try:
        return list_run_logs(run_id)
    except Exception as e:
        raise e

@router.post("/{run_id}/logs")
async def add_run_log(run_id: str, data: CreateRunLog) -> SerializedRunLog:
    try:
        data.run_id = ObjectIdStr(run_id)
        return await create_run_log(data)
    except Exception as e:
        raise e

@router.get("/{run_id}/events")
async def get_run_events(run_id: str) -> list[SerializedRunEvent]:
    try:
        return list_run_events(run_id)
    except Exception as e:
        raise e

@router.post("/{run_id}/events")
async def add_run_event(run_id: str, event_data: CreateRunEvent) -> SerializedRunEvent:
    try:
        event_data.run_id = ObjectIdStr(run_id)
        return await create_run_event(event_data)
    except Exception as e:
        raise e

class RunStatusUpdate(BaseModel):
    status: RunStatus

@router.post("/{run_id}/status")
async def post_run_status(run_id: str, status_update: RunStatusUpdate) -> SerializedRun:
    try:
        return await update_run_status(run_id, status_update.status)
    except Exception as e:
        raise e