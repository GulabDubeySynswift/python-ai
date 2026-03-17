from fastapi import FastAPI
from database.database import engine, Base
from routers import user_router
from routers import chroma_router
from routers import chat_router
from routers import auth_router
from core.ai_config import init_ai

tags_metadata = [
    {
        "name": "Auth",
        "description": "Authentication endpoints for logging in and accessing the current user profile.",
    },
    {
        "name": "Users",
        "description": "Operations on application users (CRUD). Requires authentication.",
    },
    {
        "name": "Chroma",
        "description": "PDF upload, embedding, and vector search endpoints backed by ChromaDB.",
    },
    {
        "name": "Chat",
        "description": "Chat endpoints that interact with the LLM using stored conversation/context.",
    },
]

app = FastAPI(
    title="Python AI Backend",
    description=(
        "Backend API for authentication, user management, PDF ingestion/search with ChromaDB, "
        "and LLM-powered chat. Use the **Authorize** button with a Bearer token to access "
        "protected endpoints."
    ),
    version="1.0.0",
    openapi_tags=tags_metadata,
)

Base.metadata.create_all(bind=engine)


@app.on_event("startup")
def startup_event():
    init_ai()

@app.get("/", tags=["Health"], summary="Health check", description="Simple health-check endpoint to verify the API is running.")
def get_home():
    return {"message": "Hello World"}


app.include_router(auth_router.router)
app.include_router(user_router.router)
app.include_router(chroma_router.router)
app.include_router(chat_router.router)