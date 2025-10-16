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
from loguru import logger

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

    def _ensure_chat_table(self, cur) -> None:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
              id SERIAL PRIMARY KEY,
              user_id INTEGER NOT NULL,
              role VARCHAR(20) NOT NULL CHECK (role IN ('user','assistant')),
              content TEXT NOT NULL,
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_chat_messages_user_id_created_at
            ON chat_messages (user_id, created_at DESC);
        """)

    def _load_history_db(self, user_id: int) -> str:
        conn = connect()
        if not conn:
            logger.warning("BD no disponible; se usará memoria desde archivo")
            return ""
        try:
            cur = conn.cursor()
            self._ensure_chat_table(cur)
            cur.execute("""
                SELECT content
                FROM chat_messages
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, (user_id,))
            row = cur.fetchone()
            if row and row[0]:
                logger.info(f"Último mensaje recuperado desde BD para user_id={user_id}")
                return row[0]
            return ""
        except Exception as e:
            logger.error(f"Error leyendo memoria desde BD: {e}")
            return ""
        finally:
            try: cur.close()
            except: pass
            disconnect(conn)

    def _save_message_db(self, user_id: int, role: str, content: str) -> None:
        conn = connect()
        if not conn:
            logger.warning("BD no disponible al guardar; se persistirá solo en archivo")
            return
        try:
            cur = conn.cursor()
            self._ensure_chat_table(cur)
            cur.execute("""
                INSERT INTO chat_messages (user_id, role, content)
                VALUES (%s, %s, %s)
            """, (user_id, role, content))
            conn.commit()
            logger.info(f"Mensaje guardado en BD user_id={user_id}, role={role}")
        except Exception as e:
            logger.error(f"Error guardando mensaje en BD: {e}")
            try: conn.rollback()
            except: pass
        finally:
            try: cur.close()
            except: pass
            disconnect(conn)

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

    def _save_history(self, user_id: int, history: str) -> None:
        path = self._history_path(user_id)
        payload = {"history": history}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

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
        # Cargar memoria: último mensaje desde BD; si no hay, usar archivo
        last_message = self._load_history_db(user_id) or self._load_history(user_id)

        prompt = get_chat_prompt()
        response = (prompt | self.llm).invoke({
            "full_name": profile["full_name"],
            "education_level": profile["education_level"],
            "previous_experience": profile["previous_experience"],
            "main_skills": profile["main_skills"],
            "area_of_interest": profile["area_of_interest"],
            "digital_level": profile["digital_level"],
            "chat_history": last_message,
            "input": user_input,
        })
        response_text = response if isinstance(response, str) else getattr(response, "content", str(response))

        # Persistencia en BD (dos filas por interacción)
        self._save_message_db(user_id, "user", user_input)
        self._save_message_db(user_id, "assistant", response_text)

        # Backup en archivo para /history
        file_history = self._load_history(user_id)
        updated_history = (
            (file_history + "\n" if file_history else "")
            + f"Usuario: {user_input}\nCoach: {response_text}"
        )
        self._save_history(user_id, updated_history)

        return response_text