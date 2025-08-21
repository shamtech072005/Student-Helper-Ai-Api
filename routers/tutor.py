# routers/tutor.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .database import get_db
from .models import User
from .utils import get_current_user, search_milvus, generate_tutor_response_with_llm, update_usage

router = APIRouter(prefix="/tutor", tags=["Tutor Q&A"])

class TutorQuestion(BaseModel):
    file_id: int
    question: str

@router.post("/ask")
def ask_tutor(q: TutorQuestion, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check usage limits
    if current_user.plan == "Free" and current_user.usage_count >= 10:
        raise HTTPException(status_code=403, detail="Free plan limit of 10 Q&A per day exceeded.")

    # 1. Search Milvus for relevant chunks
    retrieved_chunks = search_milvus(q.file_id, q.question)
    
    # 2. Call LLM with context and question
    response = generate_tutor_response_with_llm(retrieved_chunks, q.question)
    
    # 3. Update usage
    update_usage(current_user, "qna", db)
    
    return {"answer": response}