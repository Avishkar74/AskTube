from typing import Tuple, List, Dict, Any
from fastapi import FastAPI, HTTPException

from ..schemas.chat import ChatRequest
from ..core.logging import logger
from ..core.config import get_settings
from pathlib import Path
import sys


async def chat_once(app: FastAPI, payload: ChatRequest) -> Tuple[str, List[Dict[str, Any]] | None, Dict[str, Any]]:
    youtube_url = payload.youtube_url
    video_id = payload.video_id
    message = payload.message

    if not (youtube_url or video_id):
        raise HTTPException(status_code=400, detail="Provide youtube_url or video_id")

    # Prefer provided video_id; else derive from URL in ConversationManager usage
    # For simplicity, we'll use video_id as conversation key; if only URL was given, we might extract id in processing.
    vid_key = video_id or (youtube_url or "unknown").split("v=")[-1]

    backend = (payload.backend or "ollama").lower()
    model = payload.model
    settings = get_settings()
    use_rag = payload.use_rag if payload.use_rag is not None else settings.USE_RAG

    # Lazy import to avoid backend/model initialization at app startup
    # Ensure project root is on sys.path so we can import existing modules
    _ROOT = Path(__file__).resolve().parents[3]
    if str(_ROOT) not in sys.path:
        sys.path.append(str(_ROOT))
    from conversation_manager import ConversationManager  # noqa: WPS433
    manager = ConversationManager(backend_type=backend, model=model, use_rag=use_rag)

    # For this minimal version, we don't attach transcript here; we assume it is indexed or stored via the processing flow.
    # Future: auto-index flow like chat_cli if needed.
    answer = manager.chat(user_id="api_user", video_id=vid_key, message=message)

    # Citations are embedded inline like [cN]; we can parse later. For now, return None list.
    citations = None
    meta = {"backend": backend, "model": model or "default", "use_rag": use_rag}
    return answer, citations, meta
