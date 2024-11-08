import asyncio
from app.utils.socket_manager import connect_socketio
from app.models import BotRunRequest
from fastapi import FastAPI, BackgroundTasks
from app.agent_service import register_agent, send_heartbeat, execute_bot, stop_bot

app = FastAPI()

# Register the agent with the Orchestrator on startup
@app.on_event("startup")
async def startup_event():
		connect_socketio()
		await register_agent()
		asyncio.create_task(send_heartbeat())

@app.post("/run")
async def run_bot(request: BotRunRequest, background_tasks: BackgroundTasks):
    """Run a bot script in the background"""
    background_tasks.add_task(execute_bot, request.bot_id, request.bot_script, request.run_id)

    return {"status": "running", "bot_id": request.bot_id, "run_id": request.run_id}

@app.post("/stop")
async def stop_running_bot(bot_id: str):
    """Stop a running bot."""
    await stop_bot(bot_id)
    return {"status": "stopped", "bot_id": bot_id}
