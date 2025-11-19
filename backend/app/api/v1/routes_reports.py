from typing import Optional, List
from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse

from ...repositories import report_repo
from ...db.gridfs import get_gridfs_bucket, download_bytes
from ...schemas.report import ReportIn, ReportOut, ReportMeta
from ...services.rag_store import has_index as rag_has_index, get_index_stats, get_chunks
from ...services.transcript_service import get_transcript_segments_by_id
from ...schemas.video import TranscriptSegment, RagChunk

router = APIRouter()


@router.post(
    "/process",
    response_model=ReportOut,
    summary="Start processing a video",
    description="Create a processing job for the given YouTube URL; artifacts are generated in background.",
)
async def create_process(request: Request, background_tasks: BackgroundTasks, payload: ReportIn):
    youtube_url = payload.youtube_url
    force_reindex = bool(payload.force_reindex)
    if not youtube_url:
        raise HTTPException(status_code=400, detail="youtube_url is required")

    db = request.app.state.db
    if db is None:
        raise HTTPException(status_code=503, detail="Database not configured")

    report_id = await report_repo.insert_report(db, youtube_url)
    # Lazy import of processing service so that heavy LLM modules are not imported during startup
    from ...services.processing_service import process_report  # noqa: WPS433
    background_tasks.add_task(process_report, request.app, report_id, youtube_url, force_reindex)
    return {"report_id": report_id}


@router.get(
    "/reports",
    response_model=dict,
    summary="List reports",
    description="List processed reports with optional filter by video_id and pagination via limit/offset.",
)
async def list_reports(request: Request, video_id: Optional[str] = None, limit: int = 50, offset: int = 0):
    db = request.app.state.db
    if db is None:
        raise HTTPException(status_code=503, detail="Database not configured")
    total = await report_repo.count_reports(db, video_id=video_id)
    items = await report_repo.list_reports(db, video_id=video_id, limit=limit, offset=offset)
    return {"items": items, "total": total}


@router.get(
    "/reports/{report_id}",
    response_model=ReportMeta,
    summary="Get report",
    description="Fetch a single report by its ID including status and artifacts.",
)
async def get_report(request: Request, report_id: str):
    db = request.app.state.db
    if db is None:
        raise HTTPException(status_code=503, detail="Database not configured")
    doc = await report_repo.get_by_id(db, report_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Report not found")
    return doc


@router.get(
    "/reports/{report_id}/download",
    summary="Download report artifact",
    description="Download the HTML or PDF artifact for the given report.",
)
async def download_report(request: Request, report_id: str, type: str = "html"):
    db = request.app.state.db
    if db is None:
        raise HTTPException(status_code=503, detail="Database not configured")
    doc = await report_repo.get_by_id(db, report_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Report not found")

    artifacts = (doc or {}).get("artifacts") or {}
    key = "html_file_id" if type == "html" else "pdf_file_id"
    file_id = artifacts.get(key)
    if not file_id:
        raise HTTPException(status_code=404, detail=f"No {type} available for this report")

    bucket = get_gridfs_bucket(db)
    data = await download_bytes(bucket, file_id)

    media_type = "text/html" if type == "html" else "application/pdf"
    filename = f"{doc.get('video_id') or 'report'}.{ 'html' if type=='html' else 'pdf'}"
    return StreamingResponse(iter([data]), media_type=media_type, headers={
        "Content-Disposition": f"attachment; filename={filename}"
    })


@router.get(
    "/videos/{video_id}/rag",
    response_model=dict,
    summary="RAG status",
    description="Check if a FAISS index exists for a video and return chunk count.",
)
async def get_rag_status(video_id: str):
    """Simple RAG readiness/status for a given video id.

    Returns: { has_index: bool, chunk_count: int }
    """
    exists = rag_has_index(video_id)
    stats = get_index_stats(video_id) if exists else {"chunk_count": 0}
    return {"video_id": video_id, "has_index": exists, **stats}


@router.get(
    "/videos/{video_id}/transcript",
    response_model=List[TranscriptSegment],
    summary="Transcript segments",
    description="Fetch transcript segments directly from YouTube (text, start, duration).",
)
async def get_video_transcript(video_id: str, language: str = "en"):
    try:
        segs = get_transcript_segments_by_id(video_id, language=language)
        # Pydantic will coerce dicts into TranscriptSegment
        return segs
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Transcript fetch failed: {e}")


@router.get(
    "/videos/{video_id}/chunks",
    response_model=dict,
    summary="RAG chunks",
    description="List all stored RAG chunks for a video including start/end seconds and indices.",
)
async def get_video_chunks(video_id: str):
    if not rag_has_index(video_id):
        return {"items": [], "chunk_count": 0}
    items = get_chunks(video_id)
    return {"items": items, "chunk_count": len(items)}
