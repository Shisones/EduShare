from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class QuestionCreate(BaseModel):
    title: str
    content: str
    tags: List[str]
    authorId: str  # Use string instead of ObjectId

    class Config:
        from_attributes = True

class QuestionDetail(BaseModel):
    id: str
    title: str
    content: str
    tags: List[str]
    authorId: str  # Use string instead of ObjectId
    createdAt: datetime
    answers: List[str]  # Use string instead of ObjectId

    class Config:
        from_attributes = True

class QuestionUpdate(BaseModel):
    authorId: str  # Use string instead of ObjectId
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None

    class Config:
        from_attributes = True
