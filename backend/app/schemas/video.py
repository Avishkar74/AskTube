"""Pydantic models for transcript segments and RAG chunks."""

from typing import Optional
from pydantic import BaseModel


class TranscriptSegment(BaseModel):
    """Single transcript unit with start time and duration (seconds)."""
    text: str
    start: float
    duration: float


class RagChunk(BaseModel):
    """Stored RAG chunk with optional timing and index within the corpus."""
    text: str
    start_sec: Optional[float] = None
    end_sec: Optional[float] = None
    chunk_index: int
