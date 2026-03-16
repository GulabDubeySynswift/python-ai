from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.database import SessionLocal
from models.user_model import User
from schemas.user_schema import UserLogin
from utils.hash import verify_password
from utils.jwt_handler import create_access_token
from middlewares.auth_middleware import get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/login",
    summary="User login",
    description="Authenticate a user with email and password and return a JWT access token.",
)
def login(user: UserLogin, db: Session = Depends(get_db)):

    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid email")

    if not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Invalid password")

    token = create_access_token({"user_id": db_user.id})

    return {
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer",
    }


@router.get(
    "/profile",
    summary="Get current user profile",
    description="Return information about the currently authenticated user based on the provided JWT token.",
)
def get_profile(current_user=Depends(get_current_user)):

    return {
        "message": "Protected route accessed",
        "user": current_user,
    }