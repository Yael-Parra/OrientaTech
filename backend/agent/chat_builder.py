import os
import json
from typing import Dict, Any, Optional

# LangChain / LLM
from langchain_groq import ChatGroq
from langchain.chains import LLMChain

# Prompt
from agent.prompt_chat import get_chat_prompt

# DB access (use same strategy as langchain.py)
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_connection import connect, disconnect

class ChatBuilder:
    """
    Builder que:
    - Detecta el usuario logeado (via user_id recibido por capa de rutas/servicio).
    - Busca sus datos en la BD.
    - Recupera y persiste un buffer de conversación por usuario.
    - Compone el prompt y envía al LLM de Groq.
    """

    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")

        self.llm = ChatGroq(
            groq_api_key=self.groq_api_key,
            model_name="llama-3.1-8b-instant",
            temperature=0.3,
            max_tokens=1500,
        )

        # Carpeta para almacenar memoria de chat por usuario (persistencia simple)
        self.base_chat_dir = os.path.join(os.path.dirname(__file__), "..", "user_chat")
        os.makedirs(self.base_chat_dir, exist_ok=True)

    def _history_path(self, user_id: int) -> str:
        return os.path.join(self.base_chat_dir, f"user_{user_id}_history.json")

    def _load_history(self, user_id: int) -> str:
        path = self._history_path(user_id)
        if not os.path.exists(path):
            return ""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("history", "")
        except Exception:
            return ""

    def _save_history(self, user_id: int, history: str) -> None:
        path = self._history_path(user_id)
        payload = {"history": history}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def _get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """
        Obtiene el perfil del usuario desde la tabla user_personal_info.
        Si no existe, devuelve un set de valores por defecto sensatos.
        """
        conn = connect()
        if conn is None:
            # valores por defecto si la conexión falla
            return {
                "full_name": "Usuario",
                "education_level": "secondary",
                "previous_experience": "Sin experiencia registrada",
                "main_skills": "Por definir",
                "area_of_interest": "Tecnología",
                "digital_level": "basic",
            }

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT full_name, education_level, previous_experience,
                       main_skills, area_of_interest, digital_level
                FROM user_personal_info
                WHERE user_id = %s
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                return {
                    "full_name": "Usuario",
                    "education_level": "secondary",
                    "previous_experience": "Sin experiencia registrada",
                    "main_skills": "Por definir",
                    "area_of_interest": "Tecnología",
                    "digital_level": "basic",
                }

            return {
                "full_name": row[0] or "Usuario",
                "education_level": row[1] or "secondary",
                "previous_experience": row[2] or "Sin experiencia registrada",
                "main_skills": row[3] or "Por definir",
                "area_of_interest": row[4] or "Tecnología",
                "digital_level": row[5] or "basic",
            }
        except Exception:
            return {
                "full_name": "Usuario",
                "education_level": "secondary",
                "previous_experience": "Sin experiencia registrada",
                "main_skills": "Por definir",
                "area_of_interest": "Tecnología",
                "digital_level": "basic",
            }
        finally:
            try:
                cursor.close()
            except Exception:
                pass
            disconnect(conn)

    def send_user_message(self, user_id: int, user_input: str) -> str:
        """
        Flujo de conversación:
        - Cargar perfil de usuario desde BD.
        - Cargar historial previo (buffer) desde almacenamiento persistente.
        - Construir prompt y llamar al LLM.
        - Guardar respuesta y actualizar historial.
        - Devolver respuesta.
        """
        profile = self._get_user_profile(user_id)
        chat_history = self._load_history(user_id)

        prompt = get_chat_prompt()
        chain = LLMChain(llm=self.llm, prompt=prompt)

        response = chain.run(
            full_name=profile["full_name"],
            education_level=profile["education_level"],
            previous_experience=profile["previous_experience"],
            main_skills=profile["main_skills"],
            area_of_interest=profile["area_of_interest"],
            digital_level=profile["digital_level"],
            chat_history=chat_history,
            input=user_input,
        )

        # Actualizar historial (buffer conversacional persistente)
        updated_history = (
            (chat_history + "\n" if chat_history else "")
            + f"Usuario: {user_input}\nCoach: {response}"
        )
        self._save_history(user_id, updated_history)

        return response