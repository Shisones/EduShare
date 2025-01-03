from pydantic import BaseModel
from typing import List
from datetime import datetime

class QuestionCreate(BaseModel):
    title: str
    content: str
    tags: List[str]
    authorId: str  # Use string instead of ObjectId

    class Config:
        from_attributes = True

class QuestionDetail(BaseModel):
    title: str
    content: str
    tags: List[str]
    authorId: str  # Use string instead of ObjectId
    createdAt: datetime
    answers: List[str]  # Use string instead of ObjectId

    class Config:
        from_attributes = True

