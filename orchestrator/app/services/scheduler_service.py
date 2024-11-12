import asyncio
from bson import ObjectId
from croniter import croniter, CroniterBadCronError
from datetime import datetime, timedelta
from pymongo.errors import PyMongoError
from ..database import bots_collection, runs_collection
from .run_service import UpdateRun, create_run_entry, serialize_run, update_run
from .agent_service import find_available_agent
from .bot_service import serialize_bot, start_bot_run

async def schedule_bot_runs():
    while True:
        now = datetime.now()
        print(f"[Scheduler] Checking scheduled bots at {now.isoformat()}")
        try:
            bots = list(bots_collection.find({"schedule": {"$ne": None}}))
            for bot in bots:
                serialized_bot = serialize_bot(bot)
                bot_id = serialized_bot["id"]
                cron = bot["schedule"]
                try:
                    cron_iter = croniter(cron, now)
                    next_run_time = cron_iter.get_next(datetime)
                    print(f"[Scheduler] Bot {bot_id} scheduled to run at {next_run_time.isoformat()} with CRON {cron}")

                    # Check if there are any existing queued runs for this bot
                    existing_queued_runs = runs_collection.find_one({"bot_id": bot_id, "status": "queued"})
                    if existing_queued_runs:
                        print(f"[Scheduler] Existing queued run found for bot {bot_id}, skipping scheduling: {existing_queued_runs}")
                        continue

                    # Schedule the run if the next run time is not yet scheduled
                    if next_run_time > now:
                        await create_run_entry(bot_id, status="queued", start_time=next_run_time)
                except CroniterBadCronError as e:
                    print(f"[Scheduler] Invalid CRON expression for bot {bot_id}: {cron} - {e}")
                except Exception as e:
                    print(f"[Scheduler] Unexpected error while scheduling bot {bot_id}: {e}")
        except Exception as e:
            print(f"[Scheduler] Unexpected error while fetching bots: {e}")
        await asyncio.sleep(60)  # Check every minute

async def monitor_queued_runs():
    while True:
        now = datetime.now()
        print(f"[Monitor] Checking queued runs at {now.isoformat()}")
        try:
            # Find all queued runs where the start time has passed
            queued_runs = list(runs_collection.find({"status": "queued", "start_time": {"$lte": now}}))
            print(f"[Monitor] Found {len(queued_runs)} queued runs")
            for run in queued_runs:
                serialized_run = serialize_run(run)
                bot_id = serialized_run["bot_id"]
                run_id = serialized_run["id"]
                try:
                    bot = bots_collection.find_one({"_id": ObjectId(bot_id)})
                    if not bot:
                        print(f"[Monitor] Bot {bot_id} not found for queued run {run_id}")
                        continue

                    success = await start_bot_run(bot_id, run_id)
                    if not success:
                        print(f"[Monitor] Failed to start queued run {run_id}")
                except Exception as e:
                    print(f"[Monitor] Unexpected error while starting run {run_id}: {e}")
        except Exception as e:
            print(f"[Monitor] Unexpected error while fetching queued runs: {e}")
        await asyncio.sleep(5)  # Check every minute