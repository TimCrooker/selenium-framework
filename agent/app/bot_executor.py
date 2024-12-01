from bots.complex_bot import ComplexBot
from bots.google_bot import GoogleBot
from .utils.communication import update_run_status
from .utils.config import ORCHESTRATOR_URL
from .utils.socket_manager import send_agent_log, send_run_event

class BotExecutor:
    def __init__(self):
        self.current_bot = None

    async def run_bot_script(self, bot_id, bot_script, run_id):
        if self.current_bot is not None:
            await send_agent_log("Another bot is already running.")
            return
        await send_run_event(run_id, "running")
        await send_agent_log(f"Running bot script: {bot_script}")

        try:
            if bot_script == "google_bot":
                bot_instance = GoogleBot(run_id=run_id, socket_url=ORCHESTRATOR_URL, orchestrator_url=ORCHESTRATOR_URL)
            elif bot_script == "complex_bot":
                bot_instance = ComplexBot(run_id=run_id, socket_url=ORCHESTRATOR_URL, orchestrator_url=ORCHESTRATOR_URL)
            else:
                await update_run_status(run_id, "error")
                return

            self.current_bot = bot_instance
            await bot_instance.run()

            await update_run_status(run_id, "completed")
            await send_agent_log("Bot script completed successfully.")
        except Exception as e:
            print(f"Error running bot script: {str(e)}")
            await send_run_event(run_id, "error", payload={"error": str(e)})
            await update_run_status(run_id, "error")
        finally:
            await self.stop_bot(bot_id, run_id)

    async def stop_bot(self, bot_id, run_id):
        if self.current_bot:
            await self.current_bot.handle_termination()
            self.current_bot = None
