from sqlalchemy.orm import Session
from repositories import user_repository

def create_user_service(db: Session, user):
    return user_repository.create_user(db, user)

def get_users_service(db: Session):
    return user_repository.get_users(db)

def get_user_service(db: Session, user_id):
    return user_repository.get_user(db, user_id)

def delete_user_service(db: Session, user_id):
    return user_repository.delete_user(db, user_id)