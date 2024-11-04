from bson.objectid import ObjectId
from ..database import bots_collection
from ..utils.socket_manager import sio
import asyncio

def serialize_bot(bot) -> dict:
    bot['id'] = str(bot['_id'])
    del bot['_id']
    return bot

async def update_bot_status(bot_id: str, status: str):
    bots_collection.update_one({"_id": ObjectId(bot_id)}, {"$set": {"status": status}})
    # Emit status change event asynchronously
    await sio.emit('bot_status', {'bot_id': bot_id, 'status': status}, room=bot_id)
