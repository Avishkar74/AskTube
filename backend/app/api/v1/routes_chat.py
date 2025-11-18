from fastapi import APIRouter, Request, HTTPException

from ...schemas.chat import ChatRequest, ChatResponse
from ...services.chat_service import chat_once

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: Request, payload: ChatRequest):
    try:
        answer, citations, meta = await chat_once(request.app, payload)
        return ChatResponse(answer=answer, citations=citations, meta=meta)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
