import httpx

from .agent_service import get_agent_url

def serialize_bot(bot):
    """Convert a MongoDB document to a dictionary for JSON responses."""
    return {
        "id": str(bot["_id"]),
        "name": bot["name"],
        "script": bot.get("script", ""),
        "status": bot.get("status", "unknown"),
        "created_at": bot.get("created_at")
    }

async def start_bot_run(agent_id, bot_id, bot_script, run_id):
    """Request the agent to start the bot script."""
    agent_public_url = await get_agent_url(agent_id)
    if not agent_public_url:
        return False

    payload = {
      "bot_id": bot_id,
      "bot_script": bot_script,
      "run_id": run_id
    }

    async with httpx.AsyncClient() as client:
        try:
            # response = await client.post(f"{agent_public_url}/run", json=payload)
            response = await client.post(f"{agent_public_url}/run", json=payload)
            response.raise_for_status()

            return True
        except httpx.HTTPStatusError as e:
            # Specifically catch HTTP status errors, such as 422
            print(f"HTTP error {e.response.status_code} while starting bot on agent {agent_id}: {e.response.text}")
            return False
        except httpx.RequestError as e:
            print(f"Failed to start bot on agent {agent_id}: {e}")
            return False

