from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from loguru import logger

from agent.langchain import Chatbot
from routes.auth_simple import get_current_user

router = APIRouter(prefix="/api/chatbot", tags=["Chatbot"])

# Instancia única reutilizable del chatbot
chatbot = Chatbot()

class ChatMessageRequest(BaseModel):
    # Antes tenía user_id: int; ahora solo el mensaje
    message: str

class ChatMessageResponse(BaseModel):
    user_id: int
    response: str
    timestamp: datetime

@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    payload: ChatMessageRequest,
    current_user: dict = Depends(get_current_user)
) -> ChatMessageResponse:
    """
    Envía un mensaje del usuario autenticado al chatbot con memoria conversacional.
    """
    try:
        user_id = current_user["id"]
        logger.info(f"📩 Chatbot: mensaje recibido user_id={user_id}")
        response_text = chatbot.chat(user_id=user_id, user_input=payload.message)
        logger.info(f"📤 Chatbot: respuesta generada user_id={user_id}")
        return ChatMessageResponse(
            user_id=user_id,
            response=response_text,
            timestamp=datetime.utcnow(),
        )
    except Exception as e:
        logger.error(f"❌ Error en endpoint /api/chatbot/message: {e}")
        raise HTTPException(status_code=500, detail="Error generando respuesta del chatbot")

@router.get("/history")
async def get_history(
    current_user: dict = Depends(get_current_user)
):
    """
    Recupera el historial del usuario autenticado.
    """
    try:
        user_id = current_user["id"]
        logger.info(f"📚 Chatbot: recuperando historial user_id={user_id}")
        history_text = chatbot.builder._load_history(user_id)
        return {"user_id": user_id, "history": history_text}
    except Exception as e:
        logger.error(f"❌ Error recuperando historial: {e}")
        raise HTTPException(status_code=500, detail="No se pudo recuperar el historial")