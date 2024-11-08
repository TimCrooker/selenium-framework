import socketio

from pydantic import BaseModel

# Create a separate Socket.IO server
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
sio_app = socketio.ASGIApp(sio)

# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    print('Client connected:', sid)

@sio.event
async def disconnect(sid):
    print('Client disconnected:', sid)

@sio.event
async def join(sid, data):
    bot_id = data.get('bot_id')
    if bot_id:
        await sio.enter_room(sid, bot_id)
        print(f"Client {sid} joined room {bot_id}")

@sio.event
async def leave(sid, data):
    bot_id = data.get('bot_id')
    if bot_id:
        await sio.leave_room(sid, bot_id)
        print(f"Client {sid} left room {bot_id}")






