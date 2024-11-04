from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import bots, runs
from .utils.socket_manager import sio_app

# Create a FastAPI app
app = FastAPI()

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the Socket.IO app onto the FastAPI app at the "/socket.io" path
app.mount("/socket.io", sio_app)

# Include routers
app.include_router(bots.router, prefix="/bots", tags=["bots"])
app.include_router(runs.router, prefix="/runs", tags=["runs"])
