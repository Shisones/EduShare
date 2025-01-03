from fastapi import APIRouter, HTTPException
from bson import ObjectId
from datetime import datetime
from models.QuestionModel import QuestionCreate, QuestionDetail
from config.database import db

question_router = APIRouter()

@question_router.post("/questions", response_model=QuestionDetail)
async def create_question(question: QuestionCreate):
    question_data = question.dict()
    question_data["createdAt"] = datetime.now()
    result = db.questions.insert_one(question_data)
    question_data["_id"] = str(result.inserted_id)  # Return ObjectId as string
    return question_data

@question_router.get("/questions/{question_id}", response_model=QuestionDetail)
async def get_question(question_id: str):
    question = db.questions.find_one({"_id": ObjectId(question_id)})  # Convert string to ObjectId
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    question["_id"] = str(question["_id"])  # Return ObjectId as string
    return question

