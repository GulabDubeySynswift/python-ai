from fastapi import APIRouter, Form, UploadFile, File
from pydantic import BaseModel
import tempfile
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from services.llama_index_service import query_engine
import chromadb
from services.embedding_service import create_embedding
import uuid
from utils.file_to_text import file_to_text
from utils.chunk_text import chunk_text
from agents.claude_agent import agent

router = APIRouter()

class ChromaClient:
    def __init__(self, user_id: str):
        self.client = chromadb.PersistentClient(path="./chroma_db3")
        self.collection = self.client.get_or_create_collection(
            name=f"documents_{user_id}",
            metadata={"embedding_model": "voyage-large-2"}
        )
    def add_document(self, text: str, thread_id: str):
        embedding = create_embedding(text=text)
        self.collection.add(
            embeddings=[embedding],
            documents=[text],
            ids=[str(uuid.uuid4())],
            metadatas=[{"thread_id": thread_id}]
        )
    def search_document(self, query: str, thread_id: str):
        embedding = create_embedding(text=query)
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=3,
            where={"thread_id": thread_id}
        )
        return results
    def delete_document(self, document_id: str):
        self.collection.delete(ids=[document_id])
    def delete_all_documents(self):
        self.collection.delete_all()
    def get_document(self, document_id: str):
        return self.collection.get(ids=[document_id])
    def get_all_documents(self):
        return self.collection.get_all()
    def get_document_count(self):
        return self.collection.count()
    def get_document_ids(self):
        return self.collection.get_ids()

class AgentRequest(BaseModel):
    user_id: str
    thread_id: str
    message: str

@router.post("/agent")
async def doc_agent(user_id: str = Form(...),
        thread_id: str = Form(...),
        message: str = Form(...),
        file: UploadFile = File(...)
    ):
    
    chroma_client = ChromaClient(user_id)
    file_text = await file_to_text(file)

    chunks = chunk_text(file_text)
    for chunk in chunks:
        chroma_client.add_document(chunk, thread_id)

    results = chroma_client.search_document(message, thread_id)
    return {"message": results, "chunks": len(chunks)}

class ConversationBuffer:
    def __init__(self):
        self.buffer = []
    
    def add(self, question, answer):
        self.buffer.append({
            "question": question,
            "answer": answer
        })

    def get(self): 
        return self.buffer

    def get_text(self):
        text = ""
        for item in self.buffer:
            text +=f"User: {item['question']}\nAssistant: {item['answer']}\n"
        
        return text

    def clear(self):
        self.buffer = []

    def size(self):
        return len(self.buffer)

# ✅ Global storage (basic version)
buffers = {}  # key = thread_id

@router.post("/agent/ask")
async def ask_agent(
        workspace_id: str = Form(...),
        user_id: str = Form(...),
        thread_id: str = Form(...),
        message: str = Form(...),
    ):

    if user_id not in buffers:
        buffers[user_id] = {}

    if thread_id not in buffers[user_id]:
        buffers[user_id][thread_id] = ConversationBuffer()

    buffer = buffers[user_id][thread_id]

    config = {
        "configurable": {
            "thread_id": f"{user_id}:{thread_id}",
            "workspace_id": workspace_id,
            "user_id": user_id,
        }
    }
    response = agent.invoke({
        "messages": [
            {"role": "user", "content": message}
        ]
    }, config)
    answer = response["messages"][-1].content

    if buffer.size() >= 3: 
        # buffer.buffer = buffer.buffer[-5:]
        buffer.clear()

    buffer.add(message, answer)
    
    return {"chats": buffer.get()}