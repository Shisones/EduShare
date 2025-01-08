from fastapi import APIRouter, HTTPException
from bson import ObjectId
from datetime import datetime
from models.AnswerModel import AnswerCreate, AnswerDetail, AnswerUpdate
from config.database import db
from typing import List

answer_router = APIRouter()

# Utility: Validate user existence
def validate_user(user_id: str):
    if not db.users.find_one({"_id": ObjectId(user_id)}):
        raise HTTPException(status_code=400, detail=f"User with ID {user_id} does not exist")

# Utility: Validate question existence
def validate_question(question_id: str):
    if not db.questions.find_one({"_id": ObjectId(question_id)}):
        raise HTTPException(status_code=404, detail=f"Question with ID {question_id} does not exist")

# Utility: Add answer to user's answers list
def add_answer_to_user(user_id: str, answer_id: str):
    result = db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$push": {"answers": answer_id}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to update user's answers")

# Utility: Add answer to question's answers list
def add_answer_to_question(question_id: str, answer_id: str):
    result = db.questions.update_one(
        {"_id": ObjectId(question_id)},
        {"$push": {"answers": answer_id}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to update question's answers")

# Utility: Remove answer ID from user's answers list
def remove_answer_from_user(user_id: str, answer_id: str):
    result = db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$pull": {"answers": answer_id}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to remove answer from user's answers list")

# Utility: Remove answer ID from question's answers list
def remove_answer_from_question(question_id: str, answer_id: str):
    result = db.questions.update_one(
        {"_id": ObjectId(question_id)},
        {"$pull": {"answers": answer_id}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to remove answer from question's answers list")

# Create an answer
@answer_router.post("/answers", response_model=AnswerDetail)
async def create_answer(answer: AnswerCreate):
    # Validate user and question existence
    validate_user(answer.authorId)
    validate_question(answer.questionId)

    answer_data = answer.dict()
    answer_data["createdAt"] = datetime.now()
    answer_data["upvotes"] = 0
    answer_data["isBestAnswer"] = False

    # Insert answer into the database
    result = db.answers.insert_one(answer_data)
    answer_id = str(result.inserted_id)

    # Add answer ID to user's answers list
    add_answer_to_user(answer.authorId, answer_id)

    # Add answer ID to question's answers list
    add_answer_to_question(answer.questionId, answer_id)

    answer_data["id"] = answer_id  # Add the answer ID to the response
    return answer_data

# Fetch answers by question ID
@answer_router.get("/answers/question/{question_id}", response_model=List[AnswerDetail])
async def fetch_answers_by_question(question_id: str):
    validate_question(question_id)
    answers = db.answers.find({"questionId": question_id})
    answer_list = []

    for answer in answers:
        answer["id"] = str(answer["_id"])
        del answer["_id"]
        answer_list.append(answer)

    # if not answer_list:
    #     raise HTTPException(status_code=404, detail="No answers found for this question")
    return answer_list

# Fetch answer by answer ID
@answer_router.get("/answers/{answer_id}", response_model=AnswerDetail)
async def fetch_answer_by_id(answer_id: str):
    answer = db.answers.find_one({"_id": ObjectId(answer_id)})
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")

    answer["id"] = str(answer["_id"])
    del answer["_id"]
    return answer

# Update an answer
@answer_router.put("/answers/{answer_id}", response_model=AnswerDetail)
async def update_answer(answer_id: str, updated_answer: AnswerUpdate):
    # Retrieve the existing answer from the database
    answer = db.answers.find_one({"_id": ObjectId(answer_id)})
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")
    # Validate that the user and question exist before updating

    # Ensure you can't change the answer ID or question ID
    updated_data = updated_answer.dict(exclude_unset=True)

    # Update the answer in the database
    result = db.answers.find_one_and_update(
        {"_id": ObjectId(answer_id)},
        {"$set": updated_data},
        return_document=True
    )

    if not result:
        raise HTTPException(status_code=404, detail="Answer not found")

    # Convert ObjectId to string and return the updated answer
    result["id"] = str(result["_id"])
    del result["_id"]
    return result

# Delete an answer
@answer_router.delete("/answers/{answer_id}", response_model=dict)
async def delete_answer(answer_id: str):
    try:
        # Find the answer
        answer = db.answers.find_one({"_id": ObjectId(answer_id)})
        if not answer:
            raise HTTPException(status_code=404, detail="Answer not found")

        # Find the user and validate
        validate_user(answer["authorId"])

        # Find the question and validate
        validate_question(answer["questionId"])

        # Delete the answer
        result = db.answers.delete_one({"_id": ObjectId(answer_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Answer not found")

        # Cascade delete: Remove the answer from the user's list
        remove_answer_from_user(answer["authorId"], answer_id)

        # Cascade delete: Remove the answer from the question's list
        remove_answer_from_question(answer["questionId"], answer_id)

        return {"message": "Answer deleted successfully", "answer_id": answer_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


