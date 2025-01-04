from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AnswerCreate(BaseModel):
    content: str
    questionId: str
    authorId: str  # Use string for user ID validation

    class Config:
        from_attributes = True

class AnswerUpdate(BaseModel):
    content: Optional[str] = None
    isBestAnswer: Optional[bool] = None  # Allow toggling the "best answer" flag
    upvotes: Optional[int] = None
    class Config:
        from_attributes = True

class AnswerDetail(BaseModel):
    id: str
    content: str
    questionId: str
    authorId: str
    createdAt: datetime
    upvotes: int
    isBestAnswer: bool

    class Config:
        from_attributes = True

