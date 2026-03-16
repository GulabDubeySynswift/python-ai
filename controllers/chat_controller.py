from services.chat_service import ChatService

class ChatController:

    def __init__(self, db):
        self.service = ChatService(db)

    def chat(self, conversation_id, message):

        return self.service.chat(conversation_id, message)