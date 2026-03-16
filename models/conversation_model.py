from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database.database import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer)
    title = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)