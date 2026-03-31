from sqlalchemy import Column, String, Enum, JSON, BigInteger, TIMESTAMP, text
from database.database import Base

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(BigInteger, primary_key=True, index=True)
    workspace_id = Column(String(50))
    user_id = Column(String(50))
    thread_id = Column(String(50))
    role = Column(Enum("user", "assistant"))
    message = Column(JSON)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))