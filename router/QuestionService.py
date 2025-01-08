from fastapi import APIRouter, HTTPException
from bson import ObjectId
from datetime import datetime
from typing import List
from models.QuestionModel import QuestionCreate, QuestionDetail, QuestionUpdate
from config.database import db
import pymongo
question_router = APIRouter()

# Utility: Validate user existence
def validate_user(user_id: str):
    if not db.users.find_one({"_id": ObjectId(user_id)}):
        raise HTTPException(status_code=400, detail=f"User with ID {user_id} does not exist")

# Utility: Add question ID to user's questions
def add_question_to_user(user_id: str, question_id: str):
    result = db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$push": {"questions": question_id}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to update user's questions")

# Utility: Remove question ID from user's questions list
def remove_question_from_user(user_id: str, question_id: str):
    result = db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$pull": {"questions": question_id}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to remove question from user's questions list")

# Create a question
@question_router.post("/questions", response_model=QuestionDetail)
async def create_question(question: QuestionCreate):
    validate_user(question.authorId)

    question_data = question.dict()
    question_data["createdAt"] = datetime.now()
    question_data["answers"] = []

    # Insert into questions collection
    result = db.questions.insert_one(question_data)
    question_id = str(result.inserted_id)

    # Add question ID to user's questions
    add_question_to_user(question.authorId, question_id)

    question_data["id"] = question_id
    return question_data

# Fetch questions by user ID
@question_router.get("/questions/user/{user_id}", response_model=List[QuestionDetail])
async def fetch_questions_by_user(user_id: str):
    validate_user(user_id)
    questions = db.questions.find({"authorId": user_id})
    question_list = []

    for question in questions:
        question["id"] = str(question["_id"])
        question["answers"] = [str(answer) for answer in question["answers"]]
        del question["_id"]
        question_list.append(question)

    # if not question_list:
    #     raise HTTPException(status_code=404, detail="No questions found for this user")
    return question_list

# Fetch question by question ID
@question_router.get("/questions/{question_id}", response_model=QuestionDetail)
async def fetch_question_by_id(question_id: str):
    question = db.questions.find_one({"_id": ObjectId(question_id)})
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    validate_user(question["authorId"])

    question["id"] = str(question["_id"])
    question["answers"] = [str(answer) for answer in question["answers"]]
    del question["_id"]
    return question
    # raise HTTPException(status_code=400, detail="Invalid question ID format")

# Fetch all questions
@question_router.get("/questions", response_model=List[QuestionDetail])
async def fetch_all_questions():
    questions = db.questions.find()
    question_list = []

    for question in questions:
        question["id"] = str(question["_id"])  # Add question ID to the response
        question["answers"] = [str(answer) for answer in question["answers"]]  # Convert ObjectId to str
        del question["_id"]  # Remove MongoDB's internal `_id` field
        question_list.append(question)

    # if not question_list:
    #     raise HTTPException(status_code=404, detail="No questions found")
    return question_list


@question_router.put("/questions/{question_id}", response_model=QuestionDetail)
async def update_question(question_id: str, updated_data: QuestionUpdate):
    # Validate the question ID
    question = db.questions.find_one({"_id": ObjectId(question_id)})
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Validate the user ID (author of the question)
    validate_user(question["authorId"])

    # Prepare the update data
    update_fields = {key: value for key, value in updated_data.dict().items() if value is not None}

    # Prevent updating `id` and `authorId`
    if "id" in update_fields in update_fields:
        raise HTTPException(status_code=400, detail="Cannot update `id` fields")

    # Update the question in MongoDB
    result = db.questions.find_one_and_update(
        {"_id": ObjectId(question_id)},
        {"$set": update_fields},
        return_document=pymongo.ReturnDocument.AFTER
    )

    if not result:
        raise HTTPException(status_code=500, detail="Failed to update the question")

    # Convert ObjectId and answers for response
    result["id"] = str(result["_id"])
    result["answers"] = [str(answer) for answer in result["answers"]]
    del result["_id"]  # Remove the internal MongoDB `_id` field

    return result


@question_router.delete("/questions/{question_id}", response_model=dict)
async def delete_question(question_id: str):
    try:
        # Find the question
        question = db.questions.find_one({"_id": ObjectId(question_id)})
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        # Validate user existence
        validate_user(question["authorId"])

        # Remove the question from user's question list
        remove_question_from_user(question["authorId"], question_id)

        # Delete the question from the questions collection
        result = db.questions.delete_one({"_id": ObjectId(question_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Failed to delete the question")

        return {"message": "Question and associated answers deleted successfully", "question_id": question_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

