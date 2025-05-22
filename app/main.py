from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import timedelta

from app.config import settings
from app.routes import auth, chats, messages, branches, websockets
from app.services.cache_service import CacheService
from app.db.db import create_tables

# Import FastAPICache
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Create FastAPI app
app = FastAPI(
    title="Chat API with Branching",
    description="A microservice-based chat backend using FastAPI that allows users to create chat conversations and branch conversations from any point in the chat history.",
    version="1.0.0",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(chats.router)
app.include_router(messages.router)
app.include_router(branches.router)
app.include_router(websockets.router)

@app.on_event("startup")
def startup_event():
    create_tables()
    
    # Initialize FastAPICache
    FastAPICache.init(
        InMemoryBackend(),
        prefix="fastapi-cache",
        expire=timedelta(minutes=5),
    )
    
    # Rest of your startup code

@app.on_event("shutdown")
async def shutdown_event():
    logging.info("Application shutting down")

@app.get("/")
async def root():
    return {"message": "Welcome to the Chat API with Branching"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 