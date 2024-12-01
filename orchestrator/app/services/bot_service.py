import httpx
from croniter import croniter, CroniterBadCronError
from bson.objectid import ObjectId
from pymongo.errors import PyMongoError

from app.services.agent_service import find_available_agent
from app.services.run_service import UpdateRun, update_run
from app.database import bots_collection
from app.utils.socket_manager import sio

def serialize_bot(bot):
    return {
        "id": str(bot["_id"]),
        "name": bot["name"],
        "script": bot.get("script", ""),
        "schedule": bot.get("schedule", ""),
        "created_at": bot.get("created_at").isoformat() if bot.get("created_at") else None
    }

def validate_cron_expression(cron):
    try:
        croniter(cron)
        return True
    except CroniterBadCronError:
        return False

async def start_bot_run(bot_id: str, run_id: str):
    bot = bots_collection.find_one({"_id": ObjectId(bot_id)})
    if not bot:
        print(f"Bot {bot_id} not found")
        return False

    bot_script = bot.get("script")

    # find an available agent
    agent = await find_available_agent()
    if not agent:
        print(f"No available agent to run bot {bot_id}")

    agent_public_url = agent.get("public_url")
    if not agent_public_url:
        return False

    agent_id = agent["agent_id"]

    payload = {
        "bot_id": bot_id,
        "bot_script": bot_script,
        "run_id": run_id
    }

    # set the run status to starting
    await update_run(run_id, UpdateRun(status="starting", agent_id=agent_id))

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{agent_public_url}/run", json=payload)
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError as e:
            print(f"HTTP error {e.response.status_code} while starting bot on agent {agent_id}: {e.response.text}")
            return False
        except httpx.RequestError as e:
            print(f"Failed to start bot on agent {agent_id}: {e}")
            return False

async def delete_bot(bot_id):
    try:
        result = bots_collection.delete_one({"_id": ObjectId(bot_id)})
        if result.deleted_count > 0:
            await emit_bot_deleted(bot_id)
            return True
        else:
            print(f"Bot {bot_id} not found for deletion")
            return False
    except PyMongoError as e:
        print(f"Error deleting bot {bot_id}: {e}")
        return False

async def update_bot(bot_id, bot_data):
    if "schedule" in bot_data and not validate_cron_expression(bot_data["schedule"]):
        print(f"Invalid CRON expression: {bot_data['schedule']}")
        return False

    print(f"UPDATING BOT {bot_id} WITH DATA {bot_data}")

    try:
        result = bots_collection.update_one({"_id": ObjectId(bot_id)}, {"$set": bot_data})
        if result.modified_count > 0:
            await emit_bot_updated(bot_id)
            return True
        else:
            print(f"Bot {bot_id} not found or no changes made")
            return False
    except PyMongoError as e:
        print(f"Error updating bot {bot_id}: {e}")
        return False

async def emit_bot_deleted(bot_id):
    print("EMITTING BOT DELETED")
    await sio.emit('bot_deleted', {"bot_id": bot_id}, namespace='/ui')

async def emit_bot_updated(bot_id):
    bot = bots_collection.find_one({"_id": ObjectId(bot_id)})
    if not bot:
        print(f"Bot {bot_id} not found")
        return

    serialized_bot = serialize_bot(bot)
    print("EMITTING BOT UPDATED")
    await sio.emit('bot_updated', serialized_bot, namespace='/ui')

