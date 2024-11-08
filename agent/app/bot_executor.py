import os
import asyncio
from datetime import datetime

from bots.google_bot import GoogleBot
from .utils.communication import send_agent_log, send_run_event, update_agent_status, update_run_status
from .utils.config import BOTS_DIRECTORY, ORCHESTRATOR_URL

class BotExecutor:
    def __init__(self):
        self.running_process = None

    async def run_bot_script(self, bot_id, bot_script, run_id):
        await update_agent_status(status="running")
        await update_run_status(run_id, "running")
        script_path = os.path.join(BOTS_DIRECTORY, bot_script)

        await send_agent_log(f"Running bot script: {script_path}")

        try:
            # Here we create an instance of the bot class and run it directly
            if bot_script == "google_bot.py":
                self.running_bot = GoogleBot(run_id=run_id, socket_url=ORCHESTRATOR_URL, orchestrator_url=ORCHESTRATOR_URL)
                await self.running_bot.run()
            else:
                await update_run_status(run_id, "error")
                return

            # If the bot run completes successfully
            await update_run_status(run_id, "completed")
        except Exception as e:
            print(f"Error running bot script: {str(e)}")
            await send_run_event(run_id, "error", payload={"error": str(e)})
        finally:
            # After execution, mark the agent as available
            await update_agent_status(status="available")

    async def stop_bot(self, bot_id):
        """Terminate the running bot."""
        if self.running_process:
            self.running_process.terminate()
            await self.running_process.wait()
            await update_agent_status("stopped")
