from fastapi import APIRouter, HTTPException
from typing import List
from bson.objectid import ObjectId
from pydantic import BaseModel
from typing import Optional

from ..models import BotInDB
from ..database import bots_collection, runs_collection
from ..services.bot_service import serialize_bot, delete_bot, update_bot, validate_cron_expression
from ..services.run_service import queue_run, serialize_run

router = APIRouter()

@router.get("/", response_model=list[BotInDB])
def list_bots():
    bots = list(bots_collection.find())
    return [serialize_bot(bot) for bot in bots]

class RegisterBot(BaseModel):
    name: str
    script: str
    schedule: Optional[str] = None

@router.post("/")
def register_bot(bot: RegisterBot):
    bot_dict = bot.model_dump()
    if "schedule" in bot_dict and not validate_cron_expression(bot_dict["schedule"]):
        raise HTTPException(status_code=400, detail="Invalid CRON expression")
    result = bots_collection.insert_one(bot_dict)
    bot_id = str(result.inserted_id)
    # If the bot has a schedule, it will be picked up by the scheduler service
    return {"message": "Bot registered", "bot_id": bot_id}

@router.get("/{bot_id}")
def get_bot(bot_id: str):
    bot = bots_collection.find_one({"_id": ObjectId(bot_id)})
    if bot:
        return serialize_bot(bot)
    raise HTTPException(status_code=404, detail="Bot not found")

@router.post("/{bot_id}/runs")
async def run_bot(bot_id: str):
    run = await queue_run(bot_id)
    run_id = run.get('id')

    return {"message": f"Bot {bot_id} is queued to run", "run_id": run_id}

@router.get("/{bot_id}/runs")
def get_bot_runs(bot_id: str):
    try:
        runs = list(runs_collection.find({"bot_id": bot_id}))
        return [serialize_run(run) for run in runs]
    except Exception as e:
        print(f"Error in get_bot_runs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e

@router.post("/{bot_id}/stop")
async def stop_bot(bot_id: str):
    bot = bots_collection.find_one({"_id": ObjectId(bot_id)})
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    run = runs_collection.find_one({"bot_id": bot_id, "status": "running"})
    if not run:
        raise HTTPException(status_code=404, detail="No running instance found for this bot")

    agent_id = run.get("agent_id")
    if agent_id:
        # TODO: Placeholder for agent stop logic, depending on implementation
        return {"message": f"Bot {bot_id} has been stopped"}
    raise HTTPException(status_code=500, detail="Agent not found for the running bot instance")

@router.get("/{bot_id}/status")
async def bot_status(bot_id: str):
    bot = bots_collection.find_one({"_id": ObjectId(bot_id)})
    if bot:
        return {"bot_id": bot_id, "status": bot.get('status', 'unknown')}
    raise HTTPException(status_code=404, detail="Bot not found")

@router.delete("/{bot_id}")
async def remove_bot(bot_id: str):
    success = await delete_bot(bot_id)
    if not success:
        raise HTTPException(status_code=404, detail="Bot not found or could not be deleted")
    return {"message": "Bot deleted successfully"}

@router.put("/{bot_id}")
async def modify_bot(bot_id: str, bot: RegisterBot):
    bot_data = bot.dict()
    if "schedule" in bot_data and not validate_cron_expression(bot_data["schedule"]):
        raise HTTPException(status_code=400, detail="Invalid CRON expression")

    success = await update_bot(bot_id, bot_data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update bot or no changes made")
    # If the bot has a schedule, it will be picked up by the scheduler service
    return {"message": "Bot updated successfully"}
