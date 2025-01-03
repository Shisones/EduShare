from pydantic import BaseModel
from datetime import datetime

class AnswerCreate(BaseModel):
    content: str
    questionId: str  # Use string instead of ObjectId
    authorId: str  # Use string instead of ObjectId

    class Config:
        from_attributes = True

class AnswerDetail(BaseModel):
    content: str
    questionId: str  # Use string instead of ObjectId
    authorId: str  # Use string instead of ObjectId
    createdAt: datetime
    upvotes: int
    isBestAnswer: bool

    class Config:
        from_attributes = True

