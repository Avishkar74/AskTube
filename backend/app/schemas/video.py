from typing import Optional
from pydantic import BaseModel


class TranscriptSegment(BaseModel):
    text: str
    start: float
    duration: float


class RagChunk(BaseModel):
    text: str
    start_sec: Optional[float] = None
    end_sec: Optional[float] = None
    chunk_index: int
