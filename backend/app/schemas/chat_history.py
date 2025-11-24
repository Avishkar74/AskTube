from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from .chat import Citation

class ChatMessage(BaseModel):
    """A single message in the chat history."""
    id: str
    role: str  # 'user' or 'ai'
    content: str
    timestamp: float
    citations: Optional[List[Citation]] = None

class ChatHistory(BaseModel):
    """Chat history for a specific video."""
    video_id: str
    messages: List[ChatMessage] = Field(default_factory=list)
