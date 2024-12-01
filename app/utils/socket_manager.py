import socketio

# Create a separate Socket.IO server with logging disabled
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*', logger=False, engineio_logger=False)
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

# Socket.IO event handlers for UI namespace
@sio.event(namespace='/ui')
async def ui_connect(sid, environ):
    print('UI Client connected:', sid)

@sio.event(namespace='/ui')
async def ui_disconnect(sid):
    print('UI Client disconnected:', sid)

@sio.event(namespace='/ui')
async def ui_join(sid, data):
    bot_id = data.get('bot_id')
    if bot_id:
        await sio.enter_room(sid, bot_id, namespace='/ui')
    print(f"UI Client {sid} joined room {bot_id}")

@sio.event(namespace='/ui')
async def ui_leave(sid, data):
    bot_id = data.get('bot_id')
    if bot_id:
        await sio.leave_room(sid, bot_id, namespace='/ui')
        print(f"UI Client {sid} left room {bot_id}")

# Socket.IO event handlers for agent namespace
@sio.event(namespace='/agent')
async def agent_connect(sid, environ):
    print('Agent connected:', sid)

@sio.event(namespace='/agent')
async def agent_disconnect(sid):
    print('Agent disconnected:', sid)

@sio.event(namespace='/agent')
async def agent_join(sid, data):
    bot_id = data.get('bot_id')
    if bot_id:
        await sio.enter_room(sid, bot_id, namespace='/agent')
    print(f"Agent {sid} joined room {bot_id}")

@sio.event(namespace='/agent')
async def agent_leave(sid, data):
    bot_id = data.get('bot_id')
    if bot_id:
        await sio.leave_room(sid, bot_id, namespace='/agent')
        print(f"Agent {sid} left room {bot_id}")
