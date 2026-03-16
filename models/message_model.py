from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from database.database import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer)
    role = Column(String(10))  # user / assistant
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)