# study-assistant-backend/app/crud/files.py

from motor.motor_asyncio import AsyncIOMotorCollection
from app.models.file import FileInDB
from bson import ObjectId
from typing import Optional, List

class FileCRUD:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def create_file(self, user_id: str, filename: str) -> FileInDB:
        """Creates a new file entry in the database."""
        file_doc = {
            "user_id": user_id,
            "filename": filename,
            "text_content": None,
            "created_at": ObjectId().generation_time
        }
        result = await self.collection.insert_one(file_doc)
        file_doc["_id"] = result.inserted_id
        return FileInDB(**file_doc)

    async def get_file_by_id(self, file_id: str) -> Optional[FileInDB]:
        """Retrieves a single file document by its ID."""
        try:
            file_doc = await self.collection.find_one({"_id": ObjectId(file_id)})
            if file_doc:
                return FileInDB(**file_doc)
        except Exception:
            return None
        return None

    async def get_all_files_by_user(self, user_id: str) -> List[FileInDB]:
        """Retrieves all files uploaded by a specific user."""
        files = []
        async for file_doc in self.collection.find({"user_id": user_id}).sort("created_at", -1):
            files.append(FileInDB(**file_doc))
        return files

    async def delete_file(self, file_id: str) -> bool:
        """Deletes a file document from the database."""
        result = await self.collection.delete_one({"_id": ObjectId(file_id)})
        return result.deleted_count > 0