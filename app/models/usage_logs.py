# study-assistant-backend/app/models/usage_logs.py

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UsageLogBase(BaseModel):
    """Base model for usage log data."""
    user_id: str
    date: str  # Format: YYYY-MM-DD
    qna_count: int = 0
    flashcard_count: int = 0

class UsageLogInDB(UsageLogBase):
    """Model for a usage log stored in the database."""
    id: str = Field(alias="_id")

    class Config:
        populate_by_field_name = True
        arbitrary_types_allowed = True