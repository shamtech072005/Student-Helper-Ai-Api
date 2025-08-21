# study-assistant-backend/app/core/deps.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.security import decode_access_token
from app.crud.users import UserCRUD
from app.db.mongodb import get_mongo_db
from app.models.user import UserDB
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Annotated

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UserDB:
    """Dependency to retrieve the current authenticated user."""
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload["sub"]
    
    # Get database connection
    db = get_mongo_db()
    users_crud = UserCRUD(db.users)
    
    user = await users_crud.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return user