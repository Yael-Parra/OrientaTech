from typing import Optional
from langchain.prompts import PromptTemplate

COACH_PERSONA_INSTRUCTIONS = """
You are an empathetic and emotionally responsible employability coach specialized in helping people transition into the tech industry.
Your mission is to support users kindly, reduce anxiety, and provide concrete, actionable guidance tailored to their background.
Always respond in Spanish with a warm, respectful, and encouraging tone.

Guidelines:
- Be concise but comprehensive; prioritize clarity and actionable steps.
- Acknowledge user strengths and past experiences, even if non-tech.
- Offer practical next actions: learning paths, portfolio suggestions, networking strategies, and job search tactics.
- Adapt advice to their education level, digital skills, and areas of interest.
- Use inclusive language and avoid judgment or unrealistic promises.
- Keep responses in Spanish, even though instructions are in English.
"""

def get_chat_prompt() -> PromptTemplate:
    """
    Build a chat prompt with persona and user profile context.
    Response must be in Spanish.
    """
    template = (
        COACH_PERSONA_INSTRUCTIONS
        + "\n\n"
        + "User Profile Context:\n"
        + "- Nombre completo: {full_name}\n"
        + "- Nivel educativo: {education_level}\n"
        + "- Experiencia previa: {previous_experience}\n"
        + "- Habilidades principales: {main_skills}\n"
        + "- Área de interés: {area_of_interest}\n"
        + "- Nivel digital: {digital_level}\n"
        + "\n"
        + "Conversación previa:\n"
        + "{chat_history}\n"
        + "\n"
        + "Usuario: {input}\n"
        + "Coach:"
    )

    return PromptTemplate(
        input_variables=[
            "full_name",
            "education_level",
            "previous_experience",
            "main_skills",
            "area_of_interest",
            "digital_level",
            "chat_history",
            "input",
        ],
        template=template,
    )