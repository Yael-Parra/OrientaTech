from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

from agent.langchain import Chatbot

router = APIRouter(prefix="/api/chatbot", tags=["Chatbot"])

# Instancia única reutilizable del chatbot
chatbot = Chatbot()

class ChatMessageRequest(BaseModel):
    user_id: int
    message: str

class ChatMessageResponse(BaseModel):
    user_id: int
    response: str
    timestamp: datetime

@router.post("/message", response_model=ChatMessageResponse)
async def send_message(payload: ChatMessageRequest) -> ChatMessageResponse:
    """
    Envía un mensaje del usuario al chatbot con memoria conversacional.
    """
    try:
        logger.info(f"📩 Chatbot: mensaje recibido user_id={payload.user_id}")
        response_text = chatbot.chat(user_id=payload.user_id, user_input=payload.message)
        logger.info(f"📤 Chatbot: respuesta generada user_id={payload.user_id}")
        return ChatMessageResponse(
            user_id=payload.user_id,
            response=response_text,
            timestamp=datetime.utcnow(),
        )
    except Exception as e:
        logger.error(f"❌ Error en endpoint /api/chatbot/message: {e}")
        raise HTTPException(status_code=500, detail="Error generando respuesta del chatbot")

@router.get("/history")
async def get_history(user_id: int):
    """
    Recupera el historial de conversación (buffer) del usuario.
    Útil para testear que persiste contexto entre mensajes.
    """
    try:
        logger.info(f"📚 Chatbot: recuperando historial user_id={user_id}")
        # Acceso controlado al builder para leer el historial persistido
        history_text = chatbot.builder._load_history(user_id)  # método interno, válido para testing
        return {"user_id": user_id, "history": history_text}
    except Exception as e:
        logger.error(f"❌ Error recuperando historial: {e}")
        raise HTTPException(status_code=500, detail="No se pudo recuperar el historial")