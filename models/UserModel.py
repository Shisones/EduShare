from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserProfile(BaseModel):
    username: str
    email: EmailStr
    reputation: int
    joinDate: datetime
    bio: str
    questions: List[str]  # Use string instead of ObjectId
    answers: List[str]  # Use string instead of ObjectId

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] 
    email: Optional[str]
    password: Optional[str]
    bio: Optional[str]

