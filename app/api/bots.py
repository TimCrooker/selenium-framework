from typing import Optional
from fastapi import APIRouter, HTTPException

from app.models import SerializedBot, SerializedRun

from ..models import CreateBot, UpdateBot
from ..database import runs_collection
from ..services.bot_service import create_bot, get_bot_by_id, list_bots, delete_bot, update_bot
from ..services.run_service import queue_run, serialize_run

router = APIRouter()

@router.get("/")
def get_bots() -> list[SerializedBot]:
    return list_bots()

@router.post("/")
async def register_bot(bot: CreateBot) -> Optional[SerializedBot]:
    return await create_bot(bot)

@router.get("/{bot_id}")
def get_bot(bot_id: str) -> SerializedBot:
    return get_bot_by_id(bot_id)

@router.put("/{bot_id}")
async def modify_bot(bot_id: str, bot: UpdateBot) -> Optional[SerializedBot]:
    return await update_bot(bot_id, bot)

@router.delete("/{bot_id}")
async def remove_bot(bot_id: str) -> dict[str, str]:
    success = await delete_bot(bot_id)
    if not success:
        raise HTTPException(status_code=404, detail="Bot not found or could not be deleted")
    return {"message": "Bot deleted successfully"}

@router.get("/{bot_id}/runs")
def get_bot_runs(bot_id: str) -> list[SerializedRun]:
    try:
        runs = list(runs_collection.find({"bot_id": bot_id}))
        return [serialize_run(run) for run in runs]
    except Exception as e:
        print(f"Error in get_bot_runs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e

@router.post("/{bot_id}/runs")
async def run_bot(bot_id: str) -> dict[str, str]:
    run = await queue_run(bot_id)
    run_id = run.id

    return {"message": f"Bot {bot_id} is queued to run", "run_id": run_id}

