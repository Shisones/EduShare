from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from bson import ObjectId
from datetime import datetime, timedelta
from models.UserModel import UserCreate, UserProfile, UserLogin, UserUpdate
from config.auth import * 
from config.database import db
from typing import List

user_router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login")

# Register a new user
@user_router.post("/register", response_model=UserProfile)
async def register(user: UserCreate):
    user_data = user.dict()
    user_data["passwordHash"] = hash_password(user.password)  # Hash the password
    user_data["reputation"] = 0
    user_data["joinDate"] = datetime.now()
    user_data["questions"] = []
    user_data["answers"] = []
    user_data["bio"] = ""

    existing_user = db.users.find_one({"email": user_data["email"]})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    result = db.users.insert_one(user_data)
    user_data["_id"] = str(result.inserted_id)

    return user_data

@user_router.post("/login")
async def login(user: UserLogin):
    user_data = db.users.find_one({"username": user.username})
    if not user_data or not verify_password(user.password, user_data["passwordHash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Generate JWT token
    access_token_expires = timedelta(hours=1)
    access_token = create_access_token(data={"sub": str(user_data["_id"])}, expires_delta=access_token_expires)
    
    return {"id": str(user_data["_id"]), "access_token": access_token, "token_type": "bearer"}

@user_router.get("/{user_id}", response_model=UserProfile)
async def get_user_by_id(user_id: str):
    try:
        # Validate and convert user_id to ObjectId
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Transform the data to match the UserProfile schema
        return {
            "id": str(user["_id"]),  # Convert ObjectId to string
            "username": user["username"],
            "email": user["email"],
            "reputation": user.get("reputation", 0),
            "joinDate": user.get("joinDate"),
            "bio": user.get("bio", ""),
            "questions": [{"questionId": str(q)} for q in user.get("questions", [])],
            "answers": [{"answerId": str(a)} for a in user.get("answers", [])],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error getting user by ID: {str(e)}")


@user_router.get("/", response_model=List[UserProfile])
async def get_all_users():
    try:
        users = db.users.find()
        return [
            {
                "id": str(user["_id"]),  # Convert ObjectId to string
                "username": user["username"],
                "email": user["email"],
                "reputation": user.get("reputation", 0),
                "joinDate": user.get("joinDate"),
                "bio": user.get("bio", ""),
                "questions": [{"questionId": str(q)} for q in user.get("questions", [])],
                "answers": [{"answerId": str(a)} for a in user.get("answers", [])],
            }
            for user in users
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving users: {str(e)}")


# Update User Profile
@user_router.put("/{user_id}", response_model=UserProfile)
async def update_user(user_id: str, user: UserUpdate):
    try:
        existing_user = db.users.find_one({"_id": ObjectId(user_id)})
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        updated_data = user.dict(exclude_unset=True)  # Only update provided fields
        if "password" in updated_data:
            updated_data["passwordHash"] = hash_password(updated_data["password"]) 
            del updated_data["password"]

        db.users.update_one({"_id": ObjectId(user_id)}, {"$set": updated_data})
        updated_user = db.users.find_one({"_id": ObjectId(user_id)})
        if updated_user is None:
            raise HTTPException(status_code=404, detail="User not found after update")
        
        updated_user["_id"] = str(updated_user["_id"])
        return updated_user
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid user ID: {str(e)}")

@user_router.put("/{user_id}/reputation/{target_user_id}", response_model=UserProfile)
async def increase_reputation(user_id: str, target_user_id: str):
    try:
        user = db.users.find_one({"_id": ObjectId(user_id)})
        target_user = db.users.find_one({"_id": ObjectId(target_user_id)})
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not target_user:
            raise HTTPException(status_code=404, detail="Target user not found")
        if user_id in target_user.get("voters", []):
            raise HTTPException(status_code=400, detail="You have already increased the reputation of this user")

        updated_reputation = target_user.get("reputation", 0) + 1  # Increase reputation by 1
        db.users.update_one(
            {"_id": ObjectId(target_user_id)}, 
            {"$set": {"reputation": updated_reputation}, "$push": {"voters": user_id}}  # Add user_id to the voters list
        )
        
        # Get the updated target user data
        updated_target_user = db.users.find_one({"_id": ObjectId(target_user_id)})
        if updated_target_user is None:
            raise HTTPException(status_code=404, detail="Target user not found after update")
        
        updated_target_user["_id"] = str(updated_target_user["_id"])
        return updated_target_user  # Return updated user data with the new reputation
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error increasing reputation: {str(e)}")

# Delete User Profile
@user_router.delete("/{user_id}", response_model=dict)
async def delete_user(user_id: str):
    try:
        # Validate and convert user_id to ObjectId
        existing_user = db.users.find_one({"_id": ObjectId(user_id)})
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        db.users.delete_one({"_id": ObjectId(user_id)})
        return {"detail": "User deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid user ID: {str(e)}")



