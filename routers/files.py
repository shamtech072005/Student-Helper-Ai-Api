# routers/files.py
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import os
from .database import get_db
from .models import File as DBFile, User
from .utils import get_current_user, process_file_content, chunk_text_for_embedding, store_embeddings_in_milvus

router = APIRouter(prefix="/files", tags=["Files"])

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not file.filename.endswith(('.pdf', '.docx', '.txt')):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF, DOCX, and TXT are supported.")

    # 1. Save file to disk temporarily
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    # 2. Extract text and clean it
    text_content = process_file_content(file_path)
    if not text_content:
        raise HTTPException(status_code=500, detail="Failed to extract text from file.")

    # 3. Store file metadata in PostgreSQL
    db_file = DBFile(user_id=current_user.id, filename=file.filename, text_content=text_content)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    # 4. Generate chunks and store embeddings in Milvus
    chunks = chunk_text_for_embedding(text_content)
    # This function is a placeholder; it would call your Milvus service
    store_embeddings_in_milvus(db_file.id, chunks)

    # 5. Clean up temporary file
    os.remove(file_path)
    
    return {"message": "File uploaded and processed successfully", "file_id": db_file.id}

@router.get("/")
def list_files(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    files = db.query(DBFile).filter(DBFile.user_id == current_user.id).all()
    return [{"id": f.id, "filename": f.filename, "uploaded_at": f.created_at} for f in files]