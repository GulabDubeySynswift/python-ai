from typing import Optional, Any

from fastapi import APIRouter, Depends, Form, UploadFile, File
import json
import re
import chromadb
from sqlalchemy.orm import Session
from database.database import SessionLocal
from repositories.message_repository import MessageRepository
from services.embedding_service import create_embedding
import uuid
from utils.file_to_text import file_to_text
from utils.chunk_text import chunk_text
from agents.claude_agent import agent

router = APIRouter()


UI_JSON_INSTRUCTIONS = """You are an AI assistant that MUST return responses in structured JSON format for frontend rendering.

Output MUST be a single valid JSON object that matches this schema:

{
  "type": "text | card | table | list | mixed",
  "title": "string (optional)",
  "description": "string (optional)",
  "data": any,
  "meta": {
    "confidence": "high | medium | low"
  }
}

Rules:
- Return ONLY JSON (no markdown, no code fences, no extra text).
- If you don't know, return: {"type":"text","description":"I don't know","data":null,"meta":{"confidence":"low"}}
"""


MAX_CONTEXT_CHARS = 6000
MAX_DOC_CHARS = 1800


def _fallback_ui_json(description: str, confidence: str = "low") -> dict[str, Any]:
    return {
        "type": "text",
        "description": description,
        "data": None,
        "meta": {"confidence": confidence},
    }


def _coerce_ui_json(model_output: Any) -> dict[str, Any]:
    """
    Best-effort: parse model output to required UI JSON schema.
    Always returns a dict (never raises).
    """
    if isinstance(model_output, dict):
        obj = model_output
    else:
        text = str(model_output or "").strip()

        # Try direct JSON parse first
        try:
            obj = json.loads(text)
        except Exception:
            # Try extracting the first JSON object substring
            match = re.search(r"\{[\s\S]*\}", text)
            if not match:
                return _fallback_ui_json(text or "No data found", confidence="low")
            try:
                obj = json.loads(match.group(0))
            except Exception:
                return _fallback_ui_json(text or "No data found", confidence="low")

    if not isinstance(obj, dict):
        return _fallback_ui_json("No data found", confidence="low")

    # Normalize to schema requirements
    ui_type = obj.get("type") or "text"
    meta = obj.get("meta") if isinstance(obj.get("meta"), dict) else {}
    confidence = meta.get("confidence") or "medium"
    if confidence not in {"high", "medium", "low"}:
        confidence = "medium"

    normalized: dict[str, Any] = {
        "type": ui_type,
        "data": obj.get("data"),
        "meta": {"confidence": confidence},
    }
    if isinstance(obj.get("title"), str) and obj.get("title").strip():
        normalized["title"] = obj["title"].strip()
    if isinstance(obj.get("description"), str) and obj.get("description").strip():
        normalized["description"] = obj["description"].strip()

    # If model gave neither description nor data, provide something usable
    if "description" not in normalized and normalized.get("data") in (None, "", [], {}):
        normalized["description"] = "No data found"

    return normalized


def _build_context_from_documents(documents: list[str]) -> str:
    if not documents:
        return ""

    trimmed: list[str] = []
    for d in documents:
        if not isinstance(d, str):
            continue
        d = d.strip()
        if not d:
            continue
        if len(d) > MAX_DOC_CHARS:
            d = d[:MAX_DOC_CHARS].rstrip() + "…"
        trimmed.append(d)

    context = "\n\n".join(trimmed).strip()
    if len(context) > MAX_CONTEXT_CHARS:
        context = context[:MAX_CONTEXT_CHARS].rstrip() + "…"
    return context


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


class ChromaClient:
    def __init__(self, collection_name: str):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"embedding_model": "voyage-large-2"}
        )
    def add_document(self, text: str, metadata: dict):
        embedding = create_embedding(text=text)
        self.collection.add(
            embeddings=[embedding],
            documents=[text],
            ids=[str(uuid.uuid4())],
            metadatas=[metadata]
        )
    def search_document(self, query: str, filter: dict):
        embedding = create_embedding(text=query)
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=3,
            where=filter
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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
# ✅ Global storage (basic version)
docBuffers = {}  # key = user_id -> thread_id

@router.post("/agent")
async def doc_agent(
    workspace_id: str = Form(...),
    user_id: str = Form(...),
    thread_id: str = Form(...),
    message: str = Form(...),
    file: Optional[UploadFile] = File(None),
):
    collection_name = f"documents_workspace_{workspace_id}_user_{user_id}"

    metadata = {
        "workspace_id": workspace_id,
        "user_id": user_id,
        "thread_id": thread_id,
    }

    where_filter = {
        "$and": [
            {"workspace_id": workspace_id},
            {"user_id": user_id},
            {"thread_id": thread_id},
        ]
    }

    chroma_client = ChromaClient(collection_name)

    # ✅ Upload file & store chunks
    chunks_count = 0
    if file is not None and getattr(file, "filename", None):
        file_text = await file_to_text(file)
        chunks = chunk_text(file_text)
        chunks_count = len(chunks)

        for chunk in chunks:
            chroma_client.add_document(chunk, metadata)

    # ✅ Search relevant docs
    results = chroma_client.search_document(message, where_filter)

    # ✅ Extract documents safely
    documents = results.get("documents", [[]])[0]

    # ✅ Build context
    context = _build_context_from_documents(documents)

    # ✅ Conversation buffer setup
    if user_id not in docBuffers:
        docBuffers[user_id] = {}

    if thread_id not in docBuffers[user_id]:
        docBuffers[user_id][thread_id] = ConversationBuffer()

    buffer = docBuffers[user_id][thread_id]

    config = {
        "configurable": {
            "thread_id": f"{user_id}:{thread_id}",
            "workspace_id": workspace_id,
            "user_id": user_id,
        }
    }

    # ✅ Final prompt (IMPORTANT)
    if context:
        final_prompt = f"""{UI_JSON_INSTRUCTIONS}

Use ONLY the provided context.

Context:
{context}

User Query:
{message}
"""
    else:
        final_prompt = f"""{UI_JSON_INSTRUCTIONS}

No context is available. If you cannot answer reliably, return "I don't know" in the JSON format.

User Query:
{message}
"""

    # ✅ Agent call with context + history
    response = agent.invoke({
        "messages": [
            {"role": "user", "content": final_prompt}
        ]
    }, config)

    answer_text = response["messages"][-1].content
    answer = _coerce_ui_json(answer_text)

    # ✅ Manage buffer
    if buffer.size() >= 3:
        buffer.clear()

    buffer.add(message, answer)

    return {
        "message": answer,
        "chunks": chunks_count,
        "context_used": len(documents)
    }

# ✅ Global storage (basic version)
buffers = {}  # key = thread_id

@router.post("/agent/ask")
async def ask_agent(
        workspace_id: str = Form(...),
        user_id: str = Form(...),
        thread_id: str = Form(...),
        message: str = Form(...),
        db: Session = Depends(get_db)
    ):
    message_repo = MessageRepository(db)
    message_repo.save_chat(workspace_id, user_id, thread_id, "user",  {"text": message})
    
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
    final_prompt = f"""{UI_JSON_INSTRUCTIONS}

Return ONLY valid JSON. No extra text.

User Query:
{message}
"""

    response = agent.invoke({
        "messages": [
            {"role": "user", "content": final_prompt}
        ]
    }, config)
    answer_text = response["messages"][-1].content
    answer = _coerce_ui_json(answer_text)

    if buffer.size() >= 3: 
        # buffer.buffer = buffer.buffer[-5:]
        buffer.clear()

    buffer.add(message, answer)
    
    
    message_repo.save_chat(workspace_id, user_id, thread_id, "assistant", answer)

    return {"message": answer}


@router.post("/agent/history")
async def agent_history(
        workspace_id: str = Form(...),
        user_id: str = Form(...),
        thread_id: str = Form(...),
        limit: int = Form(100),
        db: Session = Depends(get_db)
    ):
    message_repo = MessageRepository(db)
    history = message_repo.get_chat_history(workspace_id, user_id, thread_id, limit=limit)

    messages = []
    for chat in history:
        if chat.role == "user":
            text = ""
            if isinstance(chat.message, dict):
                text = str(chat.message.get("text", ""))
            elif isinstance(chat.message, str):
                text = chat.message
            messages.append({
                "role": "user",
                "content": text
            })
        else:
            messages.append({
                "role": "assistant",
                "ui": _coerce_ui_json(chat.message),
            })

    return {"messages": messages}


@router.post("/agent/threads")
async def agent_threads(
        workspace_id: str = Form(...),
        user_id: str = Form(...),
        limit: int = Form(50),
        db: Session = Depends(get_db)
    ):
    message_repo = MessageRepository(db)
    rows = message_repo.get_threads(workspace_id, user_id, limit=limit)

    threads = []
    for row in rows:
        threads.append({
            "thread_id": row.thread_id,
            "message_count": int(row.message_count or 0),
            "last_message_at": row.last_message_at.isoformat() if row.last_message_at else None,
        })

    return {"threads": threads}