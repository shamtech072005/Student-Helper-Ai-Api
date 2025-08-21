# study-assistant-backend/main.py

from fastapi import FastAPI
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Import database connections
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.db.milvus import connect_to_milvus, disconnect_from_milvus

# Import API routers
from app.api import auth, files, ai, payments

# Initialize FastAPI app
app = FastAPI(
    title="AI Study Assistant Backend",
    description="A backend for generating flashcards, quizzes, and a tutor chat from uploaded documents.",
    version="1.0.0",
)

# Connect to databases on startup
@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()
    await connect_to_milvus()

# Disconnect from databases on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()
    await disconnect_from_milvus()

# Include API routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(files.router, prefix="/api/v1/files", tags=["Files"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI Services"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["Payments"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the AI Study Assistant API!"}