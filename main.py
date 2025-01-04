from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from router import *
from config import *

# Initialize FastAPI app and handle Middleware
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers from each service module
app.include_router(user_router, prefix="/user", tags=["User"])
app.include_router(question_router, prefix="/question", tags=["Question"])
app.include_router(answer_router, prefix="/answer", tags=["Answer"])
