# study-assistant-backend/app/api/files.py

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from app.core.deps import get_current_user
from app.models.user import UserDB
from app.crud.files import FileCRUD
from app.db.mongodb import get_mongo_db
from app.services.file_processor import process_and_embed_file
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Annotated, List
import shutil
import os

router = APIRouter()

@router.post("/upload")
async def upload_file(
    file: Annotated[UploadFile, File()], 
    current_user: Annotated[UserDB, Depends(get_current_user)],
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """
    Uploads a file, saves it, and starts the text extraction and embedding process.
    """
    files_crud = FileCRUD(db.files)
    
    # Simple check for file type based on extension
    allowed_extensions = {".pdf", ".docx", ".txt"}
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF, DOCX, and TXT are allowed."
        )

    # Save the file to a temporary location
    try:
        temp_dir = "./temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        temp_file_path = os.path.join(temp_dir, file.filename)
        
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {e}"
        )

    # Create a database record for the file
    new_file_db = await files_crud.create_file(str(current_user.id), file.filename)

    # Start the async processing
    # Note: For production, you would use a dedicated background task queue like Celery.
    # We'll use a simple async call for this example.
    await process_and_embed_file(
        temp_file_path, str(current_user.id), str(new_file_db.id), db
    )
    
    return {"message": "File uploaded and processing started.", "file_id": str(new_file_db.id)}


@router.get("/list")
async def list_files(
    current_user: Annotated[UserDB, Depends(get_current_user)],
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """
    Lists all files uploaded by the current user.
    """
    files_crud = FileCRUD(db.files)
    files = await files_crud.get_all_files_by_user(str(current_user.id))
    return files