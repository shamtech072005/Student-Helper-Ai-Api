# routers/flashcards.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import get_db
from .models import File, Flashcard, User
from .utils import get_current_user, generate_flashcards_with_llm, update_usage

router = APIRouter(prefix="/flashcards", tags=["Flashcards"])

@router.post("/generate/{file_id}")
def generate_cards(file_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check usage limits
    if current_user.plan == "Free" and current_user.usage_count >= 5:
        raise HTTPException(status_code=403, detail="Free plan limit of 5 flashcards per upload exceeded.")

    file = db.query(File).filter(File.id == file_id, File.user_id == current_user.id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found or not owned by user.")
    
    # 1. Call LLM to generate flashcards
    flashcards_data = generate_flashcards_with_llm(file.text_content)
    
    # 2. Store generated flashcards in PostgreSQL
    new_cards = []
    for card_data in flashcards_data:
        new_card = Flashcard(file_id=file.id, question=card_data["Q"], answer=card_data["A"])
        new_cards.append(new_card)
        db.add(new_card)

    db.commit()
    update_usage(current_user, "flashcards", db)

    return {"message": f"Generated {len(new_cards)} flashcards successfully."}

@router.get("/{file_id}")
def get_cards(file_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    flashcards = db.query(Flashcard).filter(Flashcard.file_id == file_id).all()
    return [{"question": c.question, "answer": c.answer} for c in flashcards]