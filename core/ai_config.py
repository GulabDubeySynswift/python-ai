import os
from dotenv import load_dotenv, find_dotenv

from llama_index.core import Settings
from llama_index.llms.anthropic import Anthropic
from llama_index.embeddings.voyageai import VoyageEmbedding

def _load_env() -> str:
    """
    Ensure `.env` is loaded even when the process CWD isn't the project root
    (common with uvicorn reload / Windows setups).
    Returns the resolved dotenv path ('' if not found).
    """
    dotenv_path = find_dotenv(usecwd=True)
    load_dotenv(dotenv_path=dotenv_path or None, override=False)
    return dotenv_path or ""

def init_ai():
    dotenv_path = _load_env()
    # -----------------------------
    # API Keys
    # -----------------------------
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    voyage_api_key = (
        os.getenv("VOYAGE_API_KEY")
        or os.getenv("VOYAGEAI_API_KEY")
        or os.getenv("VOYAGE_APIKEY")
    )

    if not anthropic_api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY is missing. "
            f"(cwd={os.getcwd()!r}, dotenv={dotenv_path!r})"
        )

    if not voyage_api_key:
        raise ValueError(
            "VOYAGE_API_KEY is missing (also checked VOYAGEAI_API_KEY, VOYAGE_APIKEY). "
            f"(cwd={os.getcwd()!r}, dotenv={dotenv_path!r})"
        )

    # -----------------------------
    # LLM (Claude)
    # -----------------------------
    llm = Anthropic(
        model="claude-sonnet-4-5-20250929",  # or latest
        api_key=anthropic_api_key,
        temperature=0.2
    )

    # -----------------------------
    # Embedding Model
    # -----------------------------
    embed_model = VoyageEmbedding(
        model_name="voyage-large-2",
        api_key=voyage_api_key
    )

    # -----------------------------
    # Global Settings (IMPORTANT)
    # -----------------------------
    Settings.llm = llm
    Settings.embed_model = embed_model

    return {
        "llm": llm,
        "embed_model": embed_model
    }