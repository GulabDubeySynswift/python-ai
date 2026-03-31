from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from services.embedding_service import create_embedding
import chromadb

@tool
def vector_search(query: str, config: RunnableConfig) -> str:
    """Search documents from ChromaDB (workspace/user/thread scoped)."""

    embedding = create_embedding(query)

    cfg = (config or {}).get("configurable", {}) if isinstance(config, dict) else {}
    workspace_id = cfg.get("workspace_id")
    user_id = cfg.get("user_id")
    thread_id = cfg.get("thread_id")

    # Match `routers/agent_router.py` collection naming.
    # thread_id comes in as "user:thread" from router; extract actual thread part.
    thread_part = None
    if isinstance(thread_id, str) and ":" in thread_id:
        thread_part = thread_id.split(":", 1)[1]
    elif isinstance(thread_id, str):
        thread_part = thread_id

    if not workspace_id or not user_id:
        return "Missing workspace_id/user_id in config; cannot scope vector search."

    collection_name = f"documents_workspace_{workspace_id}_user_{user_id}"
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"embedding_model": "voyage-large-2"},
    )

    where = {"$and": [{"workspace_id": str(workspace_id)}, {"user_id": str(user_id)}]}
    if thread_part:
        where["$and"].append({"thread_id": str(thread_part)})

    results = collection.query(
        query_embeddings=[embedding],
        n_results=3,
        where=where
    )

    docs = (results.get("documents") or [[]])[0] or []

    return "\n".join(docs)