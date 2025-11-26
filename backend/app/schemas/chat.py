"""Pydantic models for chat requests and responses.

`ChatRequest` models the inputs for the chat endpoint, supporting either a
`youtube_url` or a `video_id`, optional RAG parameters (`use_rag`, `top_k`,
`window`), and backend/model selection. `ChatResponse` returns the answer,
optional structured `citations` (present when RAG is used), and a `meta` block
with execution details (backend/model/parameters).
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Inbound payload for `/api/v1/chat`.

    - youtube_url/video_id: Identify the target video.
    - message: User question, possibly containing a timestamp.
    - use_rag/top_k/window: Retrieval controls (semantic or timestamp-based).
    - backend/model: LLM backend selection (e.g., `ollama` or `gemini`) and model.
    """
    youtube_url: Optional[str] = None
    video_id: Optional[str] = None
    message: str
    use_rag: Optional[bool] = None
    top_k: Optional[int] = None
    window: Optional[int] = None
    backend: Optional[str] = None  # 'ollama' | 'gemini'
    model: Optional[str] = None


class Citation(BaseModel):
    """Structured citation for a retrieved chunk used in the answer."""
    chunk_id: Optional[str] = None
    text: Optional[str] = None
    score: Optional[float] = None
    chunk_index: Optional[int] = None
    start_sec: Optional[float] = None
    end_sec: Optional[float] = None


class ChatResponse(BaseModel):
    """Response model with answer text, citations, and metadata."""
    answer: str
    citations: Optional[List[Citation]] = None
    meta: Optional[Dict[str, Any]] = None
