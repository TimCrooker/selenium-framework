import docker
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from bson.objectid import ObjectId
from pydantic import BaseModel
import socketio
import asyncio
import uuid

# Create a FastAPI app
app = FastAPI()

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a separate Socket.IO server
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio)

# Docker client
docker_client = docker.DockerClient(base_url='unix://var/run/docker.sock')

# Mount the Socket.IO app onto the FastAPI app at the "/socket.io" path
app.mount("/socket.io", socket_app)

# MongoDB client setup
client = MongoClient('mongodb://mongo:27017/')
db = client['synthetic_monitoring']
bots_collection = db['bots']
runs_collection = db['runs']

# Pydantic models
class Bot(BaseModel):
    name: str
    script: str  # Path to the bot script
    schedule: str = None  # Cron expression or interval

class BotInDB(Bot):
    id: str

class Run(BaseModel):
    bot_id: str
    status: str
    start_time: str
    end_time: str = None
    logs: str = ''
    run_id: str = None

# Helper function to convert ObjectId to string
def serialize_bot(bot) -> dict:
    bot['_id'] = str(bot['_id'])
    return bot

# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    print('Client connected:', sid)

@sio.event
async def disconnect(sid):
    print('Client disconnected:', sid)

# Update bot status and emit via Socket.IO
async def update_bot_status(bot_id: str, status: str):
    bots_collection.update_one({"_id": ObjectId(bot_id)}, {"$set": {"status": status}})
    # Emit status change event asynchronously
    await sio.emit('bot_status', {'bot_id': bot_id, 'status': status})

@app.get("/bots")
def list_bots():
    bots = list(bots_collection.find())
    return [serialize_bot(bot) for bot in bots]

@app.post("/bots")
def register_bot(bot: Bot):
    bot_dict = bot.dict()
    bot_dict['status'] = 'registered'
    result = bots_collection.insert_one(bot_dict)
    bot_id = str(result.inserted_id)
    return {"message": "Bot registered", "bot_id": bot_id}

@app.get("/bots/{bot_id}")
def get_bot(bot_id: str):
    bot = bots_collection.find_one({"_id": ObjectId(bot_id)})
    if bot:
        return serialize_bot(bot)
    else:
        raise HTTPException(status_code=404, detail="Bot not found")

@app.post("/bots/{bot_id}/run")
async def run_bot(bot_id: str, background_tasks: BackgroundTasks):
    bot = bots_collection.find_one({"_id": ObjectId(bot_id)})
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    run_id = str(uuid.uuid4())
    await update_bot_status(bot_id, "running")
    # Start the bot container in the background
    background_tasks.add_task(start_bot_container, bot, run_id)
    return {"message": f"Bot {bot_id} is running", "run_id": run_id}

def start_bot_container(bot, run_id):
    try:
        # Build the image name
        image_name = "yourusername/bot"  # Replace with your actual image name

        # Environment variables for the bot
        env_vars = {
            "RUN_ID": run_id,
            "ORCHESTRATOR_URL": "http://orchestrator:8000",
            "MONGO_URI": "mongodb://mongo:27017/"
        }

        # Start the container
        container = docker_client.containers.run(
            image=image_name,
            command=["python3", f"/app/{bot['script']}", "--run_id", run_id],
            environment=env_vars,
            network="synthetic-monitoring-monitoring",  # Docker Compose network name
            detach=True,
            name=f"bot_{bot['_id']}_{run_id}"
        )

        # Wait for the container to finish
        exit_status = container.wait()
        if exit_status['StatusCode'] == 0:
            update_bot_status(str(bot['_id']), "completed")
        else:
            update_bot_status(str(bot['_id']), "error")
    except Exception as e:
        update_bot_status(str(bot['_id']), "error")
        print(f"Error running bot container: {e}")

@app.get("/bots/{bot_id}/status")
def bot_status(bot_id: str):
    bot = bots_collection.find_one({"_id": ObjectId(bot_id)})
    if bot:
        return {"bot_id": bot_id, "status": bot.get('status', 'unknown')}
    else:
        raise HTTPException(status_code=404, detail="Bot not found")

# Endpoint to retrieve logs for a specific run
@app.get("/bots/{bot_id}/runs/{run_id}")
def get_run_logs(bot_id: str, run_id: str):
    run = runs_collection.find_one({"run_id": run_id})
    if run:
        return {
            "run_id": run_id,
            "bot_id": bot_id,
            "status": run.get('status', 'unknown'),
            "start_time": run.get('start_time'),
            "end_time": run.get('end_time'),
            "logs": run.get('logs', '')
        }
    else:
        raise HTTPException(status_code=404, detail="Run not found")

# Function to broadcast logs (not fully implemented here)
def broadcast_log(run_id: str, event_data: dict):
    asyncio.create_task(sio.emit('bot_log', {'run_id': run_id, 'event_data': event_data}))
