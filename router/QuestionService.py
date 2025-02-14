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


# Utility: Remove answer ID from user's answers list
def remove_answer_from_user(user_id: str, answer_id: str):
    result = db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$pull": {"answers": answer_id}}  # Remove the answer from the user's list by its string ID
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to remove answer from user's answers list")

# Utility: Remove answer ID from question's answers list
def remove_answer_from_question(question_id: str, answer_id: str):
    result = db.questions.update_one(
        {"_id": ObjectId(question_id)},
        {"$pull": {"answers": answer_id}}  # Remove the answer from the question's list by its string ID
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to remove answer from question's answers list")
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



@question_router.get("/questions", response_model=List[dict])
async def fetch_all_questions():
    # Aggregation pipeline to join questions with the users collection to get author details
    pipeline = [
        {
            "$addFields": {
                "authorId": {"$toObjectId": "$authorId"}  # Convert authorId from string to ObjectId
            }
        },
        {
            "$lookup": {
                "from": "users",  # The users collection
                "localField": "authorId",  # The field in the questions collection that links to users
                "foreignField": "_id",  # The field in the users collection that links to questions
                "as": "author"  # The resulting field that will contain the user data
            }
        },
        {
            "$unwind": "$author"  # Flatten the array created by $lookup
        },
        {
            "$project": {
                "_id": 0,  # Exclude the internal MongoDB _id from the response
                "id": {"$toString": "$_id"},  # Convert ObjectId to string for the question ID
                "title": 1,
                "content": 1,
                "tags": 1,
                "createdAt": 1,
                "authorId": {"$toString": "$authorId"},
                "authorName": "$author.username",  # Get the author's username
                "answers": 1
            }
        }
    ]

    try:
        # Execute the aggregation pipeline
        questions = db.questions.aggregate(pipeline)
        question_list = []

        for question in questions:
            # Ensure the answers are converted to strings
            question["answers"] = [str(answer) for answer in question["answers"]]  # Convert ObjectId to str
            question_list.append(question)

        if not question_list:
            raise HTTPException(status_code=404, detail="No questions found")

        return question_list

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

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

        # Find all answers associated with the question
        answers = db.answers.find({"questionId": question_id})

        # Delete each answer associated with the question
        for answer in answers:
            answer_id = str(answer["_id"])

            # Remove the answer from the user's list of answers
            remove_answer_from_user(answer["authorId"], answer_id)

            # Remove the answer from the question's list of answers
            remove_answer_from_question(question_id, answer_id)

            # Delete the answer from the answers collection
            db.answers.delete_one({"_id": ObjectId(answer_id)})

        # Remove the question from the user's question list
        remove_question_from_user(question["authorId"], question_id)

        # Delete the question from the questions collection
        result = db.questions.delete_one({"_id": ObjectId(question_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Failed to delete the question")

        return {"message": "Question and associated answers deleted successfully", "question_id": question_id}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@question_router.get("/questions/details/{question_id}", response_model=dict)
async def fetch_question_with_answers(question_id: str):
    try:
        # Fetch the question document
        question = db.questions.find_one({"_id": ObjectId(question_id)})
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        # Fetch the author's name (question author)
        author = db.users.find_one({"_id": ObjectId(question["authorId"])}, {"username": 1})
        if not author:
            raise HTTPException(status_code=404, detail="Author not found")

        # Fetch answers and include their full details
        answer_ids = question.get("answers", [])
        answers = list(db.answers.find({"_id": {"$in": [ObjectId(aid) for aid in answer_ids]}}))
        if not answers:
            answers = []

        # Format answers with the author's name
        formatted_answers = []
        for answer in answers:
            # Fetch the author's name for each answer
            answer_author = db.users.find_one({"_id": ObjectId(answer["authorId"])}, {"username": 1})
            if not answer_author:
                raise HTTPException(status_code=404, detail="Answer author not found")
            
            formatted_answers.append({
                "id": str(answer["_id"]),
                "content": answer["content"],
                "questionId": str(answer["questionId"]),
                "authorId": str(answer["authorId"]),
                "authorName": answer_author["username"],  # Answer author's name
                "createdAt": answer["createdAt"],
                "upvotes": answer["upvotes"],
                "isBestAnswer": answer["isBestAnswer"],
            })

        # Prepare the response
        response = {
            "questionId": str(question["_id"]),
            "authorId": str(question["authorId"]),
            "authorName": author["username"],  # Question author's name
            "title": question["title"],
            "content": question["content"],
            "tags": question["tags"],
            "createdAt": question["createdAt"],
            "answers": formatted_answers,
        }
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail="An error occurred: " + str(e))

