from models.chat_message_model import ChatMessage
from models.message_model import Message
from sqlalchemy import func

class MessageRepository:

    def __init__(self, db):
        self.db = db

    def save_chat(self, workspace_id, user_id, thread_id, role, message):
        try:
            chat = ChatMessage(
                workspace_id=workspace_id,
                user_id=user_id,
                thread_id=thread_id,
                role=role,
                message=message
            )
            self.db.add(chat)
            self.db.commit()
        finally:
            self.db.close()

    def get_chat_history(self, workspace_id, user_id, thread_id, limit=10):
        try:
            chats = (
                self.db.query(ChatMessage)
                .filter_by(
                    workspace_id=workspace_id,
                    user_id=user_id,
                    thread_id=thread_id
                )
                .order_by(ChatMessage.created_at.asc())
                .limit(limit)
                .all()
            )

            return chats
        finally:
            self.db.close()

    def get_threads(self, workspace_id, user_id, limit=50):
        try:
            rows = (
                self.db.query(
                    ChatMessage.thread_id,
                    func.max(ChatMessage.created_at).label("last_message_at"),
                    func.count(ChatMessage.id).label("message_count")
                )
                .filter_by(
                    workspace_id=workspace_id,
                    user_id=user_id
                )
                .group_by(ChatMessage.thread_id)
                .order_by(func.max(ChatMessage.created_at).desc())
                .limit(limit)
                .all()
            )
            return rows
        finally:
            self.db.close()
        
    def create(self, conversation_id, role, content):

        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content
        )

        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)

        return message


    def get_last_messages(self, conversation_id, limit=10):

        return (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .all()
        )