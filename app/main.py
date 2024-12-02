from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.api import agents, bots, runs
from app.utils.socket_manager import sio_app
from .services.agent_service import monitor_agents
from .services.scheduler_service import schedule_bot_runs, monitor_queued_runs
from .services.run_service import cleanup_stuck_runs
from app.database import agents_collection, runs_collection, run_events_collection, run_logs_collection

# Create a FastAPI app
app = FastAPI()

# Start the agent monitoring task
scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def startup_event() -> None:
    await agents_collection.create_index("agent_id", unique=True)
    await runs_collection.create_index("bot_id", unique=False)
    await run_events_collection.create_index("run_id", unique=False)
    await run_logs_collection.create_index("run_id", unique=False)

    scheduler.add_job(monitor_agents, CronTrigger.from_crontab('* * * * *'))  # Every minute
    scheduler.add_job(schedule_bot_runs, CronTrigger.from_crontab('* * * * *'))  # Every minute
    scheduler.add_job(monitor_queued_runs, CronTrigger.from_crontab('* * * * *'))  # Every minute
    scheduler.add_job(cleanup_stuck_runs, CronTrigger.from_crontab('* * * * *'))  # Every minute
    scheduler.start()



# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agents.router, prefix="/agents", tags=["agents"])
app.include_router(bots.router, prefix="/bots", tags=["bots"])
app.include_router(runs.router, prefix="/runs", tags=["runs"])

# Mount the Socket.IO app onto the FastAPI app at the "/socket.io" path
app.mount("/socket.io", sio_app)
