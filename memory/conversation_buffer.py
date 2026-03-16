class ConversationBuffer:

    def __init__(self):
        self.buffer = []

    def add(self, question, answer):
        self.buffer.append({
            "question": question,
            "answer": answer
        })

    def get_text(self):
        text = ""
        for item in self.buffer:
            text += f"User: {item['question']}\nAssistant: {item['answer']}\n"
        return text

    def clear(self):
        self.buffer = []

    def size(self):
        return len(self.buffer)