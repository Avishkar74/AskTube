"""Reports, processing, and video data endpoints.

Exposes:
- `POST /process`: enqueue processing for a YouTube URL (background pipeline).
- `GET /reports`: list reports with pagination and optional `video_id` filter.
- `GET /reports/{id}`: retrieve a single report document.
- `GET /reports/{id}/download`: stream HTML/PDF artifact from GridFS.
- `GET /videos/{video_id}/rag`: minimal index status and chunk count.
- `GET /videos/{video_id}/transcript`: transcript segments fetched on-demand.
- `GET /videos/{video_id}/chunks`: stored RAG chunks with indices and timings.
"""

from typing import Optional, List
from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse

from ...core.logging import logger
from ...repositories import report_repo
from ...db.gridfs import get_gridfs_bucket, download_bytes
from ...schemas.report import ReportIn, ReportOut, ReportMeta
from ...services.rag_store import has_index as rag_has_index, get_index_stats, get_chunks
from ...services.transcript_service import get_transcript_segments_by_id, extract_video_id
from ...schemas.video import TranscriptSegment, RagChunk
from ...services.processing_service import process_report

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
        logger.error("Database not configured during /process request")
        raise HTTPException(status_code=503, detail="Database not configured")

    logger.info(f"Received processing request for URL: {youtube_url} (force_reindex={force_reindex})")
    
    # Extract video_id immediately for early validation and UI responsiveness
    try:
        video_id = extract_video_id(youtube_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    report_id = await report_repo.insert_report(db, youtube_url, video_id=video_id)
    logger.info(f"Created report {report_id} for video {video_id}, queuing background task")
    
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
    "/reports/{report_id}/pdf/ai-notes",
    summary="Download AI Notes PDF",
    description="Generate and download a PDF of AI-generated summary and detailed notes.",
)
async def download_ai_notes_pdf(request: Request, report_id: str):
    """Download AI-generated notes as PDF."""
    db = request.app.state.db
    if db is None:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    doc = await report_repo.get_by_id(db, report_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Report not found")
    
    video_id = doc.get("video_id", "unknown")
    video_title = doc.get("title", video_id)
    youtube_url = doc.get("youtube_url", "")
    
    # Get summary and notes from artifacts subdocument
    artifacts = doc.get("artifacts", {})
    summary = artifacts.get("summary", "No summary available.")
    notes = artifacts.get("notes", "No notes available.")

    
    # Generate PDF
    from ...services.pdf_exporter import EnhancedPDFExporter
    exporter = EnhancedPDFExporter()
    
    try:
        pdf_bytes = exporter.generate_ai_notes_pdf(
            video_id=video_id,
            video_title=video_title,
            video_url=youtube_url,
            summary=summary,
            notes=notes
        )
    except Exception as e:
        logger.error(f"Failed to generate AI notes PDF: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
    
    # Clean filename
    safe_filename = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_filename = safe_filename[:100]  # Limit length
    filename = f"{safe_filename}_AI_Notes.pdf" if safe_filename else f"{video_id}_AI_Notes.pdf"
    
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get(
    "/reports/{report_id}/pdf/uploaded-notes",
    summary="Download Uploaded Notes PDF",
    description="Generate and download a PDF of uploaded handwritten notes images.",
)
async def download_uploaded_notes_pdf(request: Request, report_id: str):
    """Download uploaded handwritten notes as PDF."""
    db = request.app.state.db
    if db is None:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    doc = await report_repo.get_by_id(db, report_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Report not found")
    
    video_id = doc.get("video_id")
    if not video_id:
        raise HTTPException(status_code=400, detail="Video ID not found in report")
    
    video_title = doc.get("title", video_id)
    
    # Get uploaded files
    from pathlib import Path
    upload_dir = Path("data/uploads") / video_id
    
    if not upload_dir.exists():
        raise HTTPException(status_code=404, detail="No uploaded notes found for this video")
    
    uploaded_files = []
    for file_path in upload_dir.glob("*"):
        if file_path.is_file() and file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            uploaded_files.append({
                "filename": file_path.name,
                "path": str(file_path)
            })
    
    if not uploaded_files:
        raise HTTPException(status_code=404, detail="No uploaded notes found for this video")
    
    # Sort by filename
    uploaded_files.sort(key=lambda x: x['filename'])
    
    # Generate PDF
    from ...services.pdf_exporter import EnhancedPDFExporter
    exporter = EnhancedPDFExporter()
    
    try:
        pdf_bytes = exporter.generate_uploaded_notes_pdf(
            video_id=video_id,
            video_title=video_title,
            uploaded_files=uploaded_files
        )
    except Exception as e:
        logger.error(f"Failed to generate uploaded notes PDF: {e}")
        print(f"DEBUG ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
    
    # Clean filename
    title_str = video_title if video_title else video_id
    safe_filename = "".join(c for c in title_str if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_filename = safe_filename[:100]  # Limit length
    filename = f"{safe_filename}_Uploaded_Notes.pdf" if safe_filename else f"{video_id}_Uploaded_Notes.pdf"
    
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


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
