from database.database import SessionLocal
from models.user_model import User
from utils.hash import hash_password

def run():

    db = SessionLocal()

    users = [
        User(name="John Doe", email="john@example.com", password=hash_password("12345678")),
        User(name="Jane Doe", email="jane@example.com", password=hash_password("12345678")),
        User(name="Admin", email="admin@example.com", password=hash_password("12345678"))
    ]

    db.add_all(users)
    db.commit()

    print("Users seeded successfully")