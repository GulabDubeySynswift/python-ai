from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Header
from database.chroma_client import collection
from services.embedding_service import create_embedding
import uuid
from pypdf import PdfReader
from services.chunk_service import chunk_text
from services.llm_service import ask_claude
from agents.claude_agent import agent
from memory.memory_manager import MemoryManager
from agents.claude_agent import llm
from services.llama_index_service import query_engine
import tempfile
import os
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from utils.count_tokens import validate_tokens

memory = MemoryManager(llm=llm)

router = APIRouter(
    prefix="/chroma",
    tags=["Chroma"],
)


@router.post(
    "/upload-pdf",
    summary="Upload and index a PDF",
    description=(
        "Upload a PDF file, extract its text, chunk it, compute embeddings, and store them in ChromaDB. "
        "The workspace is identified by the `X-Workspace-Id` header."
    ),
)
async def upload_pdf(file: UploadFile, workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id")):

    if workspace_id is None:
        return {"error": "Workspace ID is required"}

    reader = PdfReader(file.file)

    text = ""
    for page in reader.pages:
        text += page.extract_text()

    chunks = chunk_text(text)

    for chunk in chunks:

        embedding = create_embedding(chunk)

        collection.add(
            embeddings=[embedding],
            documents=[chunk],
            ids=[str(uuid.uuid4())],
            metadatas=[{"workspace_id": workspace_id}],
        )

    return {"message": "PDF processed", "chunks": len(chunks)}


@router.get(
    "/ask",
    summary="Semantic search in workspace",
    description=(
        "Perform a semantic search over documents in a given workspace using the query text. "
        "Returns raw results from ChromaDB including documents, distances, and metadata."
    ),
)
def ask_question(query: str, workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id")):
    
    response = query_engine.query(query)

    return str(response)

    if workspace_id is None:
        return {"error": "Workspace ID is required"}

    
    embedding = create_embedding(query)

    results = collection.query(
        query_embeddings=[embedding],
        n_results=5,
        where={"workspace_id": workspace_id},
        include=["documents", "distances", "metadatas"],
    )

    return results


@router.get(
    "/ask-claude",
    summary="Ask Claude using Chroma context",
    description=(
        "Run a semantic search in ChromaDB and send the top documents as context to Claude, "
        "returning the model's answer along with the source documents."
    ),
)
def ask_question(query: str):

    embedding = create_embedding(query)

    results = collection.query(
        query_embeddings=[embedding],
        n_results=3,
    )

    docs = results["documents"][0]

    context = "\n".join(docs)

    answer = ask_claude(context, query)

    return {
        "answer": answer,
        "sources": docs,
    }


@router.get("/ask-agent")
def ask_agent(query: str, thread_id: str, user_id: int, workspace_id: Optional[str] = Header(..., alias="X-Workspace-Id")):

    config = {
        "configurable": {
            "thread_id": thread_id,
            "workspace_id": workspace_id
        }
    }
    
    # retrieve past memory
    # past_memory = memory.get_memory(user_id, query)
    past_memory = memory.retrieve_memory(user_id, query)

    print("past_memory: ", past_memory)

    prompt = f"""
Relevant past memory:
{past_memory}

User query:
{query}
"""


    response = agent.invoke({
        "messages": [
            # ("user", query)
            {"role": "user", "content": prompt}
        ],
    }, config)

    answer = response["messages"][-1].content

    # save memory
    # memory.store_memory(user_id, query, answer)
    memory.add_message(user_id, query, answer)

    return {
        "answer": answer
    }

@router.post("/ask-file-agent")
async def ask_file_agent(
    file: UploadFile = File(...),
    query: str = Form(...),
    thread_id: str = Form(...),
    user_id: int = Form(...),
    workspace_id: Optional[str] = Header(..., alias="X-Workspace-Id")
):
    # -----------------------------
    # Save uploaded file temporarily
    # -----------------------------
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        # -----------------------------
        # Load & index file (RAG)
        # -----------------------------
        documents = SimpleDirectoryReader(input_files=[tmp_path]).load_data()

        validate_tokens(documents)

        index = VectorStoreIndex.from_documents(documents)
        query_engine = index.as_query_engine()

        # -----------------------------
        # Query file + agent
        # -----------------------------
        file_response = query_engine.query(query)
        
        return {
            "query": query,
            "file_response": file_response.response
        }

    finally:
        # cleanup temp file
        os.remove(tmp_path)

@router.post(
    "/add-document",
    summary="Add a raw text document",
    description="Add a single text document to ChromaDB after computing its embedding.",
)
def add_document(text: str):
    print("Adding document...", text)
    embedding = create_embedding(text)
    doc_id = str(uuid.uuid4())

    collection.add(
        embeddings=[embedding],
        documents=[text],
        ids=[doc_id],
    )

    return {"message": "Document added", "id": doc_id}


@router.get(
    "/search",
    summary="Simple semantic search",
    description="Run a basic semantic search over all stored documents and return the raw ChromaDB results.",
)
def search_document(query: str):

    embedding = create_embedding(query)

    results = collection.query(
        query_embeddings=[embedding],
        n_results=3,
    )

    return results