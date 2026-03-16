from repositories.message_repository import MessageRepository
from services.llm_service import ask_claude

class ChatService:

    def __init__(self, db):
        self.message_repo = MessageRepository(db)

    def chat(self, conversation_id, user_message):

        # save user message
        self.message_repo.create(conversation_id, "user", user_message)

        history = self.message_repo.get_last_messages(conversation_id)

        history_text = ""
        for msg in reversed(history):
            history_text += f"{msg.role}: {msg.content}\n"

        prompt = f"""
        Conversation history:
        {history_text}

        User: {user_message}
        """

        answer = ask_claude(prompt)

        self.message_repo.create(conversation_id, "assistant", answer)

        return answer