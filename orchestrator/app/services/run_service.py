from datetime import datetime
import traceback
import docker
import asyncio

from ..database import runs_collection
from ..services.bot_service import update_bot_status
from ..utils.socket_manager import sio

docker_client = docker.DockerClient(base_url='unix://var/run/docker.sock')

async def start_bot_container(bot, run_id):
    try:
        # Build the image name
        image_name = "bot-framework:latest"  # Replace with your actual image name

        # Environment variables for the bot
        env_vars = {
            "RUN_ID": run_id,
            "ORCHESTRATOR_URL": "http://orchestrator:8000",
            "MONGO_URI": "mongodb://mongo:27017/"
        }

				# Build the command to pass the bot script
        bot_script = bot['script']
        command = [
            "--bot_script", f"/app/{bot_script}",
            "--run_id", run_id
        ]

        # Start the container
        container = docker_client.containers.run(
            image=image_name,
            command=command,
            environment=env_vars,
            network="selenium-framework_monitoring",
            detach=True,
            name=f"bot_{bot['_id']}_{run_id}"
        )

        # Store container ID in the database for future reference
        runs_collection.update_one(
            {"run_id": run_id},
            {"$set": {"container_id": container.id}},
            upsert=False
        )

    except Exception as e:
        print(f"Error in start_bot_container: {e}")
        traceback.print_exc()
        await update_bot_status(str(bot['_id']), "error")

				# Update the run status to error
        runs_collection.update_one(
						{"run_id": run_id},
						{"$set": {"status": "error", "end_time": datetime.utcnow()}},
				)