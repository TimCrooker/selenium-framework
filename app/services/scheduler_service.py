from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bson import ObjectId
from croniter import croniter, CroniterBadCronError
from datetime import datetime

from app.models import CreateRun, RunStatus, UpdateRun
from ..database import bots_collection, runs_collection
from .run_service import create_run, serialize_run, update_run
from .bot_service import serialize_bot, start_bot_run

scheduler = AsyncIOScheduler()

async def schedule_bot_runs() -> None:
    now = datetime.now()
    print(f"[Scheduler] Checking scheduled bots at {now.isoformat()}")
    try:
        bots = list(bots_collection.find({"schedule": {"$ne": None}}))
        for bot in bots:
            serialized_bot = serialize_bot(bot)
            bot_id = serialized_bot.id
            cron = bot["schedule"]
            try:
                cron_iter = croniter(cron, now)
                next_run_time = cron_iter.get_next(datetime)
                print(f"[Scheduler] Bot {bot_id} scheduled to run at {next_run_time.isoformat()} with CRON {cron}")

                # Check if there are any existing scheduled runs for this bot
                existing_scheduled_runs = runs_collection.find_one({"bot_id": bot_id, "status": RunStatus.SCHEDULED, "start_time": next_run_time})
                if existing_scheduled_runs:
                    print(f"[Scheduler] Existing scheduled run found for bot {bot_id}, skipping scheduling: {existing_scheduled_runs}")
                    continue

                # Schedule the run if the next run time is not yet scheduled
                if next_run_time > now:
                    await create_run(CreateRun(bot_id=bot_id, status=RunStatus.SCHEDULED, start_time=next_run_time))
            except CroniterBadCronError as e:
                print(f"[Scheduler] Invalid CRON expression for bot {bot_id}: {cron} - {e}")
            except Exception as e:
                print(f"[Scheduler] Unexpected error while scheduling bot {bot_id}: {e}")
    except Exception as e:
        print(f"[Scheduler] Unexpected error while fetching bots: {e}")

async def monitor_queued_runs() -> None:
    now = datetime.now()
    print(f"[Monitor] Checking queued runs at {now.isoformat()}")
    try:
        # Find all scheduled runs where the start time has passed
        scheduled_runs = list(runs_collection.find({"status": RunStatus.SCHEDULED, "start_time": {"$lte": now}}))
        print(f"[Monitor] Found {len(scheduled_runs)} scheduled runs")
        for run in scheduled_runs:
            serialized_run = serialize_run(run)
            bot_id = serialized_run.bot_id
            run_id = serialized_run.id
            try:
                await update_run(run_id, UpdateRun(status=RunStatus.QUEUED))
            except Exception as e:
                print(f"[Monitor] Unexpected error while queuing run {run_id}: {e}")

        # Find all queued runs and attempt to start them
        queued_runs = list(runs_collection.find({"status": RunStatus.QUEUED}).sort("start_time", 1))
        print(f"[Monitor] Found {len(queued_runs)} queued runs")
        for run in queued_runs:
            serialized_run = serialize_run(run)
            bot_id = serialized_run.bot_id
            run_id = serialized_run.id
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