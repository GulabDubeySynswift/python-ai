from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from schemas.message_schema import ChatRequest, ChatResponse
from controllers.chat_controller import ChatController
from database.database import SessionLocal

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/",
    response_model=ChatResponse,
    summary="Send a chat message",
    description="Send a message to the chat controller and receive an answer from the underlying LLM.",
)
def chat(request: ChatRequest, db: Session = Depends(get_db)):

    controller = ChatController(db)

    answer = controller.chat(
        request.conversation_id,
        request.message,
    )

    return ChatResponse(answer=answer)