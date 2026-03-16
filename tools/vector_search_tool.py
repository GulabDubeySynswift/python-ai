from langchain.tools import tool
from services.embedding_service import create_embedding
from database.chroma_client import collection

@tool
def vector_search(query: str) -> str:
    """Search documents from ChromaDB"""

    embedding = create_embedding(query)

    results = collection.query(
        query_embeddings=[embedding],
        n_results=3,
    )

    docs = results["documents"][0]

    return "\n".join(docs)