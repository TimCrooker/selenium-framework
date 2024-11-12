# main.py
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import agents, bots, runs
from app.utils.socket_manager import sio_app
from .services.agent_service import monitor_agents
from .services.scheduler_service import schedule_bot_runs, monitor_queued_runs

# Create a FastAPI app
app = FastAPI()

# Start the agent monitoring task
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(monitor_agents())
    asyncio.create_task(schedule_bot_runs())
    asyncio.create_task(monitor_queued_runs())

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
