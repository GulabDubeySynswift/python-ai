from database.chroma_memory import save_memory, search_memory, save_summary, search_summary
from memory.conversation_buffer import ConversationBuffer
from memory.summarizer import summarize_conversation

class MemoryManager:

    def __init__(self, llm):
        self.buffer = ConversationBuffer()
        self.llm = llm
        self.threshold = 3

    def add_message(self, user_id, question, answer):

        self.buffer.add(question, answer)

        if self.buffer.size() >= self.threshold:

            conversation_text = self.buffer.get_text()

            summary = summarize_conversation(
                self.llm,
                conversation_text
            )

            save_summary(user_id, summary)

            self.buffer.clear()

    def retrieve_memory(self, user_id, query):

        return search_summary(user_id, query)

    def get_memory(self, user_id, question):
        return search_memory(user_id, question)

    def store_memory(self, user_id, question, answer):
        save_memory(user_id, question, answer)