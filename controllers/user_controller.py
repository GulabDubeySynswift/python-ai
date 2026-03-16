from sqlalchemy.orm import Session
from services import user_service

def create_user_controller(db: Session, user):
    return user_service.create_user_service(db, user)

def get_users_controller(db: Session):
    return user_service.get_users_service(db)

def get_user_controller(db: Session, user_id):
    return user_service.get_user_service(db, user_id)

def delete_user_controller(db: Session, user_id):
    return user_service.delete_user_service(db, user_id)