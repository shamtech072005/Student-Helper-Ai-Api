# study-assistant-backend/app/api/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.models.user import UserCreate, UserDB
from app.core.security import get_password_hash, verify_password, create_access_token
from app.crud.users import UserCRUD
from app.db.mongodb import get_mongo_db
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()

@router.post("/signup", response_model=UserDB)
async def signup(user: UserCreate, db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    """Registers a new user with a hashed password."""
    users_crud = UserCRUD(db.users)
    
    existing_user = await users_crud.get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(user.password)
    new_user = await users_crud.create_user(user, hashed_password)
    
    if not new_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
        
    return new_user

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
    """Authenticates a user and returns a JWT access token."""
    users_crud = UserCRUD(db.users)
    user = await users_crud.get_user_by_email(form_data.username)
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}