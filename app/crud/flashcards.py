# study-assistant-backend/app/crud/flashcards.py

from motor.motor_asyncio import AsyncIOMotorCollection
from app.models.flashcard import FlashcardBase, FlashcardInDB
from bson import ObjectId
from typing import Optional, List

class FlashcardCRUD:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def create_flashcards(self, file_id: str, flashcards: List[FlashcardBase]) -> bool:
        """Inserts multiple flashcards linked to a single file."""
        if not flashcards:
            return False

        flashcard_docs = []
        for fc in flashcards:
            flashcard_docs.append({
                "file_id": file_id,
                "question": fc.question,
                "answer": fc.answer,
                "created_at": ObjectId().generation_time
            })
        
        result = await self.collection.insert_many(flashcard_docs)
        return len(result.inserted_ids) == len(flashcard_docs)

    async def get_flashcards_by_file_id(self, file_id: str) -> List[FlashcardInDB]:
        """Retrieves all flashcards for a specific file."""
        flashcards = []
        async for fc_doc in self.collection.find({"file_id": file_id}).sort("created_at", 1):
            flashcards.append(FlashcardInDB(**fc_doc))
        return flashcards