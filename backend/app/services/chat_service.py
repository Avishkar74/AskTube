"""Chat orchestration service.

This service implements a single-shot chat flow that answers questions about a
YouTube video using one of two strategies:

1) Retrieval-Augmented Generation (RAG): If a FAISS index exists for the
    `video_id`, top-k semantically similar chunks are retrieved or, when the
    message contains a timestamp, the chunk(s) closest to that time are selected.
    The LLM is grounded on these chunks and returns an answer with structured
    citations including chunk indices and start/end timestamps.
2) Transcript fallback: When no index exists or retrieval fails, a truncated
    transcript is used to provide a lightweight answer or a friendly failure.

The module also parses user-provided timestamps from natural formats like
`4:32`, `01:02:03`, `4m32s`, `4 minutes 32 seconds`, etc.
"""

from typing import Tuple, List, Dict, Any
from fastapi import FastAPI, HTTPException

from ..schemas.chat import ChatRequest
from ..core.logging import logger
from ..core.config import get_settings
from .llm_backend import auto_select_backend, get_backend
from .transcript_service import get_transcript_text, extract_video_id
from .rag_store import retrieve, has_index, retrieve_by_timestamp


async def chat_once(app: FastAPI, payload: ChatRequest) -> Tuple[str, List[Dict[str, Any]] | None, Dict[str, Any]]:
    """Answer a single user question about a video.

    Flow:
    - Resolve `video_id` (from payload or URL).
    - Optionally fetch transcript text (for fallback/context).
    - If RAG is enabled and an index exists, retrieve context chunks either by
      semantic similarity (`top_k`) or by a parsed timestamp with an optional
      `window` of neighboring chunks.
    - Construct a grounded prompt for the selected LLM backend and generate.
    - Return the model's answer along with structured citations (when RAG is used)
      and a `meta` block describing backend/model and retrieval parameters.
    """
    youtube_url = payload.youtube_url
    video_id = payload.video_id
    message = payload.message

    if not (youtube_url or video_id):
        raise HTTPException(status_code=400, detail="Provide youtube_url or video_id")

    # Prefer provided video_id; else derive from URL in ConversationManager usage
    # For simplicity, we'll use video_id as conversation key; if only URL was given, we might extract id in processing.
    vid_key = video_id or (youtube_url or "unknown").split("v=")[-1]

    backend = (payload.backend or "").lower()
    model = payload.model
    settings = get_settings()
    use_rag = payload.use_rag if payload.use_rag is not None else settings.USE_RAG

    # Select backend (explicit if provided, else auto)
    selected_backend = backend or None
    try:
        backend_instance = get_backend(selected_backend, model) if selected_backend else auto_select_backend("ollama", model)
        selected_backend = (selected_backend or type(backend_instance).__name__.replace("Backend", "").lower())
    except Exception as e:
        logger.warning(f"Backend selection failed: {e}")
        backend_instance = None

    # Always fetch transcript for this chat request if youtube_url is provided
    transcript_text = ""
    try:
        if youtube_url:
            transcript_text = get_transcript_text(youtube_url)[:15000]
    except Exception as te:
        logger.warning(f"Transcript fetch failed: {te}")

    # If RAG enabled and index present, retrieve top-k chunks or timestamp-targeted chunks; else fallback to transcript
    rag_chunks_text = ""
    rag_results: List[Dict[str, Any]] = []
    if use_rag and vid_key and has_index(vid_key):
        try:
            # Timestamp-aware handling
            ts = _parse_timestamp_seconds(message)
            if ts is not None:
                w = payload.window if (payload.window is not None and payload.window >= 0) else 1
                rag_results = retrieve_by_timestamp(vid_key, ts, window=w)
            else:
                k = payload.top_k or 6
                rag_results = retrieve(vid_key, message, top_k=k)
            if rag_results:
                rag_chunks_text = "\n\n".join([f"[c{i+1}] {t['text']}" for i, t in enumerate(rag_results)])
        except Exception as re:
            logger.warning(f"RAG retrieve failed: {re}")

    # Build prompt grounded on RAG or transcript
    system = (
        "You are a helpful assistant answering questions about a YouTube video.\n"
        + ("Answer STRICTLY using the provided context chunks; cite [cN].\n" if rag_chunks_text else "Use the transcript context if available. If not present, say so.\n")
    )
    context = ""
    if rag_chunks_text:
        context = f"Context Chunks (most relevant first):\n---\n{rag_chunks_text}\n---\n\n"
    elif transcript_text:
        context = f"Transcript (truncated):\n---\n{transcript_text}\n---\n\n"
    prompt = f"{system}{context}User question: {message}\nAnswer:"

    # Try primary LLM
    answer = None
    if backend_instance is not None:
        try:
            answer = backend_instance.generate(prompt, max_tokens=512, temperature=0.3)
        except Exception as e:
            logger.warning(f"LLM generate failed: {e}")
            answer = None

    if not answer:
        # Final fallback
        if transcript_text:
            answer = "Based on the transcript, here are 3 key points:\n- " + "\n- ".join([p for p in message.split()[:3]])
        else:
            answer = "I could not access the transcript to answer this question."

    # Structured citations when using RAG
    citations: List[Dict[str, Any]] | None = None
    if rag_results:
        citations = []
        for i, item in enumerate(rag_results):
            citations.append({
                "chunk_id": f"c{i+1}",
                "text": item.get("text"),
                "score": item.get("score"),
                "chunk_index": item.get("chunk_index"),
                "start_sec": item.get("start_sec"),
                "end_sec": item.get("end_sec"),
            })
    meta = {
        "backend": selected_backend or "auto",
        "model": model or "default",
        "use_rag": use_rag,
        "fallback": backend_instance is None,
        "top_k": payload.top_k,
        "window": payload.window,
    }
    return answer, citations, meta


def _parse_timestamp_seconds(message: str) -> float | None:
    """Extract a timestamp from user message and return seconds.

    Supports formats like:
    - 4:32 or 01:02:03
    - 4m32s / 4m 32s / 32s
    - '4 min 32 sec' / '4 minutes 32 seconds'
    """
    import re

    msg = message.lower()

    # h:mm:ss or m:ss
    m = re.search(r"\b(?:(\d{1,2}):)?(\d{1,2}):(\d{2})\b", msg)
    if m:
        h = int(m.group(1) or 0)
        mi = int(m.group(2))
        s = int(m.group(3))
        return float(h * 3600 + mi * 60 + s)

    # Xm Ys or Xh Ym Zs
    m = re.search(r"\b(?:(\d+)\s*h(?:ours?)?\s*)?(?:(\d+)\s*m(?:in(?:ute)?s?)?\s*)?(?:(\d+)\s*s(?:ec(?:ond)?s?)?)\b", msg)
    if m:
        h = int(m.group(1) or 0)
        mi = int(m.group(2) or 0)
        s = int(m.group(3) or 0)
        if h or mi or s:
            return float(h * 3600 + mi * 60 + s)

    # X minutes Y seconds (allow missing seconds)
    m = re.search(r"\b(\d+)\s*min(?:ute)?s?\b", msg)
    if m:
        minutes = int(m.group(1))
        s_total = minutes * 60
        m2 = re.search(r"\b(\d+)\s*sec(?:ond)?s?\b", msg)
        if m2:
            s_total += int(m2.group(1))
        return float(s_total)

    # seconds only
    m = re.search(r"\b(\d+)\s*s(?:ec(?:ond)?s?)?\b", msg)
    if m:
        return float(int(m.group(1)))

    return None
