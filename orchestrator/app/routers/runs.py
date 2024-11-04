from fastapi import APIRouter, HTTPException
from bson.objectid import ObjectId

from ..database import runs_collection

router = APIRouter()

@router.get("/{bot_id}/runs")
def get_bot_runs(bot_id: str):
    runs = list(runs_collection.find({"bot_id": bot_id}))
    return [serialize_run(run) for run in runs]

@router.get("/{bot_id}/runs/{run_id}")
def get_run_logs(bot_id: str, run_id: str):
    run = runs_collection.find_one({"run_id": run_id})
    if run:
        return serialize_run(run)

    raise HTTPException(status_code=404, detail="Run not found")

def serialize_run(run) -> dict:
    run['run_id'] = run.get('run_id', str(run['_id']))
    run['bot_id'] = run.get('bot_id')
    run['status'] = run.get('status')
    run['start_time'] = run.get('start_time')
    run['end_time'] = run.get('end_time')
    run['logs'] = run.get('logs', '')
    run['container_id'] = run.get('container_id')
    return run