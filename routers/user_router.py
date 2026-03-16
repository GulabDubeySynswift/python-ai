from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.database import SessionLocal
from controllers import user_controller
from middlewares.auth_middleware import get_current_user
from schemas.user_schema import UserCreate, UserResponse

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(get_current_user)],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/",
    response_model=UserResponse,
    summary="Create a new user",
    description="Create a new user in the system. Requires a valid Bearer token.",
)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    return user_controller.create_user_controller(db, user)


@router.get(
    "/",
    response_model=list[UserResponse],
    summary="List users",
    description="Retrieve a list of all users. Requires a valid Bearer token.",
)
def get_users(db: Session = Depends(get_db)):
    return user_controller.get_users_controller(db)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="Retrieve a single user by its numeric ID. Requires a valid Bearer token.",
)
def get_user(user_id: int, db: Session = Depends(get_db)):
    return user_controller.get_user_controller(db, user_id)


@router.delete(
    "/{user_id}",
    summary="Delete user",
    description="Delete a user by its numeric ID. Requires a valid Bearer token.",
)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    return user_controller.delete_user_controller(db, user_id)