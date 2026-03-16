import chromadb
from chromadb.config import Settings
from services.embedding_service import create_embedding 
import uuid

# client = chromadb.Client(
#     Settings(
#         persist_directory="./chroma_db"
#     )
# )

client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(
    name="chat_memory"
)

def save_summary(user_id, summary):

    embedding = create_embedding(text=summary)

    collection.add(
        ids=[str(uuid.uuid4())],
        embeddings=[embedding],
        documents=[summary],
        metadatas=[{"user_id": user_id}]
    )

def search_summary(user_id, query, top_k=3):

    query_embedding = create_embedding(text=query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"user_id": user_id}
    )

    documents = results.get("documents", [[]])[0]

    return "\n".join(documents)

def save_memory(user_id, question, answer):

    text = f"""
    User: {question}
    Assistant: {answer}
    """
    print("conversation saved: ", text)

    embedding = create_embedding(text=text)

    collection.add(
        ids=[str(uuid.uuid4())],
        embeddings=[embedding],
        documents=[text],
        metadatas=[{"user_id": user_id}]
    )

def search_memory(user_id, query, top_k=3):

    query_embedding = create_embedding(text=query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"user_id": user_id}
    )

    documents = results.get("documents", [[]])[0]

    print("conversation retrived: ", documents)

    return "\n".join(documents)