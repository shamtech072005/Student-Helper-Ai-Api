# study-assistant-backend/app/crud/usage_logs.py

from motor.motor_asyncio import AsyncIOMotorCollection
from app.models.usage_logs import UsageLogBase, UsageLogInDB
from datetime import date
from typing import Optional

class UsageLogCRUD:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def get_or_create_daily_log(self, user_id: str) -> UsageLogInDB:
        """
        Retrieves the daily usage log for a user, or creates a new one if it doesn't exist.
        """
        today_str = date.today().isoformat()
        
        log_doc = await self.collection.find_one({
            "user_id": user_id,
            "date": today_str
        })
        
        if log_doc:
            return UsageLogInDB(**log_doc)
        
        # If no log exists for today, create a new one
        new_log = {
            "user_id": user_id,
            "date": today_str,
            "qna_count": 0,
            "flashcard_count": 0
        }
        result = await self.collection.insert_one(new_log)
        new_log["_id"] = result.inserted_id
        return UsageLogInDB(**new_log)

    async def increment_qna_count(self, user_id: str) -> bool:
        """Increments the Q&A usage count for the current day."""
        today_str = date.today().isoformat()
        result = await self.collection.update_one(
            {"user_id": user_id, "date": today_str},
            {"$inc": {"qna_count": 1}},
            upsert=True
        )
        return result.modified_count > 0 or result.upserted_id is not None

    async def increment_flashcard_count(self, user_id: str) -> bool:
        """Increments the flashcard usage count for the current day."""
        today_str = date.today().isoformat()
        result = await self.collection.update_one(
            {"user_id": user_id, "date": today_str},
            {"$inc": {"flashcard_count": 1}},
            upsert=True
        )
        return result.modified_count > 0 or result.upserted_id is not None