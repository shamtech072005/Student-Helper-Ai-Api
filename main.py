# main.py
from fastapi import FastAPI
from .routers import auth, files, tutor, payments, flashcards, quizzes

app = FastAPI()

# Include routers
app.include_router(auth.router)
app.include_router(files.router)
app.include_router(tutor.router)
app.include_router(payments.router)
app.include_router(flashcards.router)
app.include_router(quizzes.router)

@app.get("/")
def read_root():
    return {"message": "Study App Backend is running!"}