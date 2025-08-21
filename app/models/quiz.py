# study-assistant-backend/app/models/quiz.py

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class QuizBase(BaseModel):
    """Base model for quiz data."""
    question_type: str  # e.g., "MCQ", "Fill-in-the-blank"
    difficulty: str     # e.g., "Easy", "Medium", "Hard"
    question: str
    options: Optional[List[str]] = None
    correct_answer: str

class QuizInDB(QuizBase):
    """Model for a quiz stored in the database."""
    id: str = Field(alias="_id")
    file_id: str
    created_at: datetime
    
    class Config:
        populate_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        arbitrary_types_allowed = True