# study-assistant-backend/app/crud/quizzes.py

from motor.motor_asyncio import AsyncIOMotorCollection
from app.models.quiz import QuizBase, QuizInDB
from bson import ObjectId
from typing import Optional, List

class QuizCRUD:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def create_quizzes(self, file_id: str, quizzes: List[QuizBase]) -> bool:
        """Inserts multiple quiz questions linked to a single file."""
        if not quizzes:
            return False

        quiz_docs = []
        for qz in quizzes:
            quiz_docs.append({
                "file_id": file_id,
                "question_type": qz.question_type,
                "difficulty": qz.difficulty,
                "question": qz.question,
                "options": qz.options,
                "correct_answer": qz.correct_answer,
                "created_at": ObjectId().generation_time
            })
        
        result = await self.collection.insert_many(quiz_docs)
        return len(result.inserted_ids) == len(quiz_docs)

    async def get_quizzes_by_file_id(self, file_id: str) -> List[QuizInDB]:
        """Retrieves all quiz questions for a specific file."""
        quizzes = []
        async for qz_doc in self.collection.find({"file_id": file_id}).sort("created_at", 1):
            quizzes.append(QuizInDB(**qz_doc))
        return quizzes