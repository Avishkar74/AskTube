"""Chat endpoint: answers questions about a video with optional RAG.

The endpoint accepts either a `youtube_url` or `video_id` and a `message`.
When RAG is enabled (globally or per-request) and an index exists, it will
retrieve context chunks either by semantic similarity or based on a parsed
timestamp plus an optional neighbor window. The response includes structured
citations when RAG contributes to the answer.
"""

from fastapi import APIRouter, Request, HTTPException

from ...schemas.chat import ChatRequest, ChatResponse
from ...services.chat_service import chat_once

router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat about a video",
    description="Ask a question about a video using either `youtube_url` or `video_id`. Supports RAG, `top_k`, and timestamp queries with `window`.",
)
async def chat_endpoint(request: Request, payload: ChatRequest):
    """Handle a single chat request and return answer + citations + meta."""
    try:
        answer, citations, meta = await chat_once(request.app, payload)
        return ChatResponse(answer=answer, citations=citations, meta=meta)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
