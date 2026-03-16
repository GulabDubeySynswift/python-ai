from langchain.tools import tool
from services.llm_service import ask_claude

@tool
def general_llm(query: str) -> str:
    """Answer general knowledge questions"""

    return ask_claude("", query)