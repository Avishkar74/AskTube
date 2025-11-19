from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class ChatRequest(BaseModel):
    youtube_url: Optional[str] = None
    video_id: Optional[str] = None
    message: str
    use_rag: Optional[bool] = None
    top_k: Optional[int] = None
    window: Optional[int] = None
    backend: Optional[str] = None  # 'ollama' | 'gemini'
    model: Optional[str] = None


class Citation(BaseModel):
    chunk_id: Optional[str] = None
    text: Optional[str] = None
    score: Optional[float] = None
    chunk_index: Optional[int] = None
    start_sec: Optional[float] = None
    end_sec: Optional[float] = None


class ChatResponse(BaseModel):
    answer: str
    citations: Optional[List[Citation]] = None
    meta: Optional[Dict[str, Any]] = None
