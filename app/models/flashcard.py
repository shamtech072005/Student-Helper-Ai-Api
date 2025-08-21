# study-assistant-backend/app/models/flashcard.py

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class FlashcardBase(BaseModel):
    """Base model for flashcard data."""
    question: str
    answer: str

class FlashcardInDB(FlashcardBase):
    """Model for a flashcard stored in the database."""
    id: str = Field(alias="_id")
    file_id: str
    created_at: datetime

    class Config:
        populate_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        arbitrary_types_allowed = True