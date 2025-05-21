from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from pymongo.errors import ConnectionFailure
import logging

from app.config import settings

# SQLite database connection
SQLALCHEMY_DATABASE_URL = settings.SQLITE_DATABASE_URL
engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

# MongoDB connection
mongodb_client = None

async def get_mongodb_client():
    global mongodb_client
    if mongodb_client is None:
        try:
            mongodb_client = AsyncIOMotorClient(settings.MONGODB_URL)
            await mongodb_client.admin.command('ping')
            logging.info("Connected to MongoDB")
        except ConnectionFailure:
            logging.error("Failed to connect to MongoDB")
            raise
    return mongodb_client

async def get_mongodb_db():
    client = await get_mongodb_client()
    return client[settings.MONGODB_DB_NAME]

# Dependency to get DB session
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close() 