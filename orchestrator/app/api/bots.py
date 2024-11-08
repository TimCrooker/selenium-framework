from fastapi import APIRouter, HTTPException
from typing import List
from bson.objectid import ObjectId

from ..models import RegisterBot, BotInDB
from ..database import bots_collection, runs_collection
from ..services.agent_service import find_available_agent
from ..services.bot_service import serialize_bot, start_bot_run
from ..services.run_service import create_run_entry, serialize_run

router = APIRouter()

@router.get("/", response_model=List[BotInDB])
def list_bots():
    bots = list(bots_collection.find())
    return [serialize_bot(bot) for bot in bots]

@router.post("/")
def register_bot(bot: RegisterBot):
    bot_dict = bot.dict()
    result = bots_collection.insert_one(bot_dict)
    bot_id = str(result.inserted_id)
    return {"message": "Bot registered", "bot_id": bot_id}

@router.get("/{bot_id}")
def get_bot(bot_id: str):
    bot = bots_collection.find_one({"_id": ObjectId(bot_id)})
    if bot:
        return serialize_bot(bot)
    else:
        raise HTTPException(status_code=404, detail="Bot not found")

@router.post("/{bot_id}/runs")
async def run_bot(bot_id: str):
    """Assign an agent to run the bot and initiate execution."""
    bot = bots_collection.find_one({"_id": ObjectId(bot_id)})
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    # Find an available agent to run the bot
    agent = await find_available_agent()
    if not agent:
        raise HTTPException(status_code=503, detail="No available agent to run the bot")

    # Create a run entry in the database
    run = await create_run_entry(bot_id, agent['agent_id'])
    run_id = run.get('id')

    # Send execution request to the assigned agent
    success = await start_bot_run(agent['agent_id'], bot_id, bot['script'], run_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to start bot execution on the agent")

    return {"message": f"Bot {bot_id} is running on agent {agent['agent_id']}", "run_id": run_id}

@router.get("/{bot_id}/runs")
def get_bot_runs(bot_id: str):
    """Get all runs for a specific bot."""
    try:
        runs = list(runs_collection.find({"bot_id": bot_id}))
        return [serialize_run(run) for run in runs]
    except Exception as e:
        print(f"Error in get_bot_runs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e

@router.post("/{bot_id}/stop")
async def stop_bot(bot_id: str):
    """Stop a running bot."""
    bot = bots_collection.find_one({"_id": ObjectId(bot_id)})
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    # Find the running instance of this bot
    run = runs_collection.find_one({"bot_id": bot_id, "status": "running"})
    if not run:
        raise HTTPException(status_code=404, detail="No running instance found for this bot")

    # Send stop command to the agent
    agent_id = run.get("agent_id")
    if agent_id:

        # TODO: Placeholder for agent stop logic, depending on implementation
        return {"message": f"Bot {bot_id} has been stopped"}
    else:
        raise HTTPException(status_code=500, detail="Agent not found for the running bot instance")

@router.get("/{bot_id}/status")
def bot_status(bot_id: str):
    """Check the current status of a bot."""
    bot = bots_collection.find_one({"_id": ObjectId(bot_id)})
    if bot:
        return {"bot_id": bot_id, "status": bot.get('status', 'unknown')}
    else:
        raise HTTPException(status_code=404, detail="Bot not found")
