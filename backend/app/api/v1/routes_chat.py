"""Chat endpoint: answers questions about a video with optional RAG.

The endpoint accepts either a `youtube_url` or `video_id` and a `message`.
When RAG is enabled (globally or per-request) and an index exists, it will
retrieve context chunks either by semantic similarity or based on a parsed
timestamp plus an optional neighbor window. The response includes structured
citations when RAG contributes to the answer.
"""

from fastapi import APIRouter, Request, HTTPException

from ...core.logging import logger
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
        logger.info(f"Chat request received for video_id={payload.video_id} (URL={payload.youtube_url})")
        answer, citations, meta = await chat_once(request.app, payload)
        return ChatResponse(answer=answer, citations=citations, meta=meta)
    except HTTPException as he:
        logger.warning(f"Chat endpoint HTTPException: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"Chat endpoint unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/chat/stream",
    summary="Stream chat about a video",
    description="Stream answer for a question about a video. Returns NDJSON.",
)
async def chat_stream_endpoint(request: Request, payload: ChatRequest):
    """Handle a streaming chat request."""
    from fastapi.responses import StreamingResponse
    from ...services.chat_service import chat_stream
    
    return StreamingResponse(
        chat_stream(request.app, payload), 
        media_type="application/x-ndjson"
    )
