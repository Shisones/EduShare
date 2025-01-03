from fastapi import APIRouter, HTTPException
from bson import ObjectId
from datetime import datetime
from models.AnswerModel import AnswerCreate, AnswerDetail
from config.database import db

answer_router = APIRouter()

@answer_router.post("/answers", response_model=AnswerDetail)
async def create_answer(answer: AnswerCreate):
    answer_data = answer.dict()
    answer_data["createdAt"] = datetime.now()
    answer_data["upvotes"] = 0
    answer_data["isBestAnswer"] = False
    result = db.answers.insert_one(answer_data)
    answer_data["_id"] = str(result.inserted_id)  # Return ObjectId as string
    return answer_data

@answer_router.get("/answers/{answer_id}", response_model=AnswerDetail)
async def get_answer(answer_id: str):
    answer = db.answers.find_one({"_id": ObjectId(answer_id)})  # Convert string to ObjectId
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")
    
    answer["_id"] = str(answer["_id"])  # Return ObjectId as string
    return answer

