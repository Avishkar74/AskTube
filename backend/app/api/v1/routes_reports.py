from typing import Optional
from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse

from ...repositories import report_repo
from ...db.gridfs import get_gridfs_bucket, download_bytes

router = APIRouter()


@router.post("/process")
async def create_process(request: Request, background_tasks: BackgroundTasks, payload: dict):
    youtube_url = payload.get("youtube_url")
    force_reindex = bool(payload.get("force_reindex", False))
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


@router.get("/reports")
async def list_reports(request: Request, video_id: Optional[str] = None, limit: int = 50):
    db = request.app.state.db
    if db is None:
        raise HTTPException(status_code=503, detail="Database not configured")
    items = await report_repo.list_reports(db, video_id=video_id, limit=limit)
    return {"items": items}


@router.get("/reports/{report_id}")
async def get_report(request: Request, report_id: str):
    db = request.app.state.db
    if db is None:
        raise HTTPException(status_code=503, detail="Database not configured")
    doc = await report_repo.get_by_id(db, report_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Report not found")
    return doc


@router.get("/reports/{report_id}/download")
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
