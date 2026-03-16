from models.message_model import Message

class MessageRepository:

    def __init__(self, db):
        self.db = db

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