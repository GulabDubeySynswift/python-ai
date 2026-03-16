import chromadb
import voyageai

from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext
from llama_index.embeddings.voyageai import VoyageEmbedding
from llama_index.llms.anthropic import Anthropic
from llama_index.core import Settings
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    raise ValueError("ANTHROPIC_API_KEY is not set")

voyageai_api_key = os.getenv("VOYAGEAI_API_KEY")

if not voyageai_api_key:
    raise ValueError("VOYAGEAI_API_KEY is not set")

Settings.llm = Anthropic(
    model="claude-sonnet-4-5-20250929",
    api_key=api_key
)
# Set API key
voyageai.api_key = voyageai_api_key
# Voyage embedding model
embed_model = VoyageEmbedding(
    model_name="voyage-large-2"
)

# connect to chroma
client = chromadb.PersistentClient(path="./chroma_db2")

# collection = client.get_or_create_collection("documents")

collection = client.get_or_create_collection(
    name="documents",
    metadata={"embedding_model": "voyage-large-2"}
)

vector_store = ChromaVectorStore(chroma_collection=collection)

storage_context = StorageContext.from_defaults(vector_store=vector_store)

index = VectorStoreIndex.from_vector_store(
    vector_store,
    embed_model=embed_model
)

query_engine = index.as_query_engine(
    similarity_top_k=3
)