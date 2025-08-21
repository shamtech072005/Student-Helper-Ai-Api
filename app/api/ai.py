# study-assistant-backend/app/api/ai.py

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from app.core.deps import get_current_user
from app.models.user import UserDB
from app.services.ai_generator import AIGenerator
from app.services.usage_tracker import UsageTracker
from app.db.mongodb import get_mongo_db
from app.db.milvus import get_milvus_collection
from app.crud.flashcards import FlashcardCRUD
from app.crud.quizzes import QuizCRUD
from app.crud.usage_logs import UsageLogCRUD
from app.crud.files import FileCRUD
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Annotated
from pydantic import BaseModel

router = APIRouter()

class FileProcessRequest(BaseModel):
    file_id: str

class TutorRequest(BaseModel):
    file_id: str
    question: str

def get_ai_generator():
    """Dependency for the AI Generator service."""
    return AIGenerator()

def get_usage_tracker(db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    """Dependency for the Usage Tracker service."""
    return UsageTracker(UsageLogCRUD(db.usage_logs))

@router.post("/flashcards")
async def generate_flashcards(
    request: FileProcessRequest,
    background_tasks: BackgroundTasks,
    current_user: Annotated[UserDB, Depends(get_current_user)],
    ai_gen: Annotated[AIGenerator, Depends(get_ai_generator)],
    usage_tracker: Annotated[UsageTracker, Depends(get_usage_tracker)],
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """
    Generates flashcards from an uploaded file.
    """
    # Check usage limits
    can_generate = await usage_tracker.check_flashcard_limit(current_user)
    if not can_generate:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="You have exceeded your flashcard generation limit. Please upgrade your plan."
        )

    # Get the file content from MongoDB
    files_crud = FileCRUD(db.files)
    file_doc = await files_crud.get_file_by_id(request.file_id)
    if not file_doc or not file_doc.text_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found or text content is not available."
        )

    # Generate and store flashcards
    flashcard_crud = FlashcardCRUD(db.flashcards)
    flashcards = ai_gen.generate_flashcards(file_doc.text_content)
    await flashcard_crud.create_flashcards(request.file_id, flashcards)
    
    # Track usage in the background
    background_tasks.add_task(usage_tracker.increment_flashcard_count, str(current_user.id))
    
    return {"message": "Flashcards generated successfully."}


@router.post("/quizzes")
async def generate_quizzes(
    request: FileProcessRequest,
    current_user: Annotated[UserDB, Depends(get_current_user)],
    ai_gen: Annotated[AIGenerator, Depends(get_ai_generator)],
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """
    Generates quiz questions from an uploaded file.
    """
    # Note: Quiz generation is only available on paid plans, so we don't check for usage.
    if current_user.plan == "free":
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Quizzes are a premium feature. Please upgrade your plan to access them."
        )
    
    files_crud = FileCRUD(db.files)
    file_doc = await files_crud.get_file_by_id(request.file_id)
    if not file_doc or not file_doc.text_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found or text content is not available."
        )

    quiz_crud = QuizCRUD(db.quizzes)
    quizzes = ai_gen.generate_quizzes(file_doc.text_content)
    await quiz_crud.create_quizzes(request.file_id, quizzes)
    
    return {"message": "Quizzes generated successfully."}


@router.post("/tutor")
async def tutor_chat(
    request: TutorRequest,
    background_tasks: BackgroundTasks,
    current_user: Annotated[UserDB, Depends(get_current_user)],
    ai_gen: Annotated[AIGenerator, Depends(get_ai_generator)],
    usage_tracker: Annotated[UsageTracker, Depends(get_usage_tracker)],
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """
    Handles a Q&A session with the AI tutor.
    """
    # Check usage limits
    can_generate = await usage_tracker.check_qna_limit(current_user)
    if not can_generate:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="You have exceeded your Q&A limit. Please upgrade your plan."
        )
    
    # Retrieve relevant text chunks from Milvus
    milvus_collection = get_milvus_collection()
    context = ai_gen.retrieve_context_from_milvus(
        milvus_collection, request.question, request.file_id
    )
    
    if not context:
        return {"response": "I don't have enough information in the notes."}
    
    # Generate the step-by-step response
    response = ai_gen.generate_tutor_response(context, request.question)
    
    # Track usage in the background
    background_tasks.add_task(usage_tracker.increment_qna_count, str(current_user.id))

    return {"response": response}