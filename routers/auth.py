# routers/auth.py
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import create_access_token
from crud.user import (
    authenticate_user,
    create_user,
    get_user_by_email,
    get_user_by_username,
)
from dependencies.database import get_db
from settings import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


@router.post("/register", status_code=201)
def register_user(request: RegisterRequest, db: Session = Depends(get_db)):
    if get_user_by_username(db, request.username) or get_user_by_email(
        db, request.email
    ):
        raise HTTPException(status_code=400, detail="Username or email already exists")
    user = create_user(db, request.username, request.email, request.password)
    return {"message": f"User {user.username} created successfully"}


@router.post("/login")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
