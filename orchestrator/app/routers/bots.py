import asyncio
from datetime import datetime
import docker
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
from bson.objectid import ObjectId
import uuid

from ..models import Bot, BotInDB
from ..database import bots_collection, runs_collection
from ..services.bot_service import serialize_bot, update_bot_status
from ..services.run_service import start_bot_container
from ..utils.socket_manager import sio

router = APIRouter()

docker_client = docker.DockerClient(base_url='unix://var/run/docker.sock')

@router.get("/", response_model=List[BotInDB])
def list_bots():
    bots = list(bots_collection.find())
    return [serialize_bot(bot) for bot in bots]

@router.post("/")
def register_bot(bot: Bot):
    bot_dict = bot.dict()
    bot_dict['status'] = 'registered'
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

@router.put("/{bot_id}")
def update_bot(bot_id: str, bot_data: Bot):
    updated_bot = bots_collection.find_one_and_update(
        {"_id": ObjectId(bot_id)},
        {"$set": bot_data.dict()},
        return_document=True
    )
    if updated_bot:
        return serialize_bot(updated_bot)
    else:
        raise HTTPException(status_code=404, detail="Bot not found")

@router.delete("/{bot_id}")
async def delete_bot(bot_id: str):
    bot = bots_collection.find_one({"_id": ObjectId(bot_id)})
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    # Stop all active containers for this bot
    active_runs = list(runs_collection.find({"bot_id": bot_id, "status": "running"}))
    for run in active_runs:
        container_id = run.get('container_id')
        if container_id:
            try:
                container = docker_client.containers.get(container_id)
                container.stop()
                container.remove()
                # Update run status
                runs_collection.update_one(
                    {"run_id": run['run_id']},
                    {"$set": {"status": "stopped", "end_time": datetime.utcnow()}},
                )
            except Exception as e:
                print(f"Error stopping container {container_id}: {e}")
                # Optionally, handle or log the error

    # Delete the bot from the database
    bots_collection.delete_one({"_id": ObjectId(bot_id)})

    # Emit bot deletion event
    await sio.emit('bot_deleted', {'bot_id': bot_id})

    return {"message": f"Bot {bot_id} has been deleted"}

@router.post("/{bot_id}/run")
async def run_bot(bot_id: str):
    bot = bots_collection.find_one({"_id": ObjectId(bot_id)})
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    run_id = str(uuid.uuid4())

		# Create a new run document in the database
    run = runs_collection.insert_one({
        "run_id": run_id,
        "bot_id": bot_id,
        "status": "starting",
        "start_time": datetime.utcnow()
    })

		# log out the run details
    print(run)

    asyncio.create_task(start_bot_container(bot, run_id))
    await update_bot_status(bot_id, "running")
    return {"message": f"Bot {bot_id} is running", "run_id": run_id}

@router.post("/{bot_id}/stop")
def stop_bot(bot_id: str):
    bot = bots_collection.find_one({"_id": ObjectId(bot_id)})
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    # Find the running container associated with the bot
    run = runs_collection.find_one({"bot_id": bot_id, "status": "running"})
    if not run:
        raise HTTPException(status_code=404, detail="No running instance found for this bot")

    container_id = run.get('container_id')
    if not container_id:
        raise HTTPException(status_code=500, detail="Container ID not found for the running bot")

    # Stop the container
    try:
        container = docker_client.containers.get(container_id)
        container.stop()
        container.remove()
        # Update run status
        runs_collection.update_one(
            {"run_id": run['run_id']},
            {"$set": {"status": "stopped", "end_time": datetime.utcnow()}},
        )
        asyncio.create_task(update_bot_status(bot_id, "stopped"))
        return {"message": f"Bot {bot_id} has been stopped"}
    except Exception as e:
        print(f"Error stopping bot container: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop the bot container")

@router.get("/{bot_id}/status")
def bot_status(bot_id: str):
    bot = bots_collection.find_one({"_id": ObjectId(bot_id)})
    if bot:
        return {"bot_id": bot_id, "status": bot.get('status', 'unknown')}
    else:
        raise HTTPException(status_code=404, detail="Bot not found")
