"""Processing pipeline to produce artifacts and build RAG index.

This orchestrates the end-to-end flow for a given YouTube URL:
- Extract video_id and transcript (text and segments when available).
- Build the FAISS index with timing-aware chunks (for RAG + timestamp UX).
- Generate summary, notes, and mindmap via existing modules.
- Export to PDF/HTML and upload resulting artifact to GridFS.
- Persist status and artifact metadata in `reports` collection.

Runs in a background task triggered by `POST /api/v1/process`.
"""

from typing import Optional, Tuple
from fastapi import FastAPI
from starlette.concurrency import run_in_threadpool

from ..repositories import report_repo
from ..db.gridfs import get_gridfs_bucket, upload_bytes
from ..core.logging import logger
from .transcript_service import extract_video_id, get_transcript_text, get_transcript_segments
from .rag_store import build_index
"""Processing service: orchestrates transcript extraction and artifact generation.

Heavy LLM-related modules are imported lazily inside the function to avoid
delaying API startup (health/status endpoints should respond quickly).
"""
from .pdf_exporter import EnhancedPDFExporter


async def process_report(app: FastAPI, report_id: str, youtube_url: str, force_reindex: bool = False) -> None:
    """Process a report end-to-end and persist artifacts/status.

    Parameters:
    - app: FastAPI application (for access to Mongo state).
    - report_id: ID in the `reports` collection created by the API layer.
    - youtube_url: Full YouTube URL provided by the user.
    - force_reindex: Reserved for future logic to rebuild an existing index.
    """
    db = app.state.db
    if db is None:
        logger.error("Database not configured; cannot process report")
        return

    await report_repo.update_status(db, report_id, "running")

    try:
        logger.info(f"Starting processing for report {report_id} (URL: {youtube_url})")

        # 1) Extract transcript and basic meta (backend-local)
        video_id = extract_video_id(youtube_url)
        logger.debug(f"Extracted video_id: {video_id}")
        
        # Run transcript fetching in threadpool as it might be slow/blocking
        transcript_text = await run_in_threadpool(get_transcript_text, youtube_url)
        logger.info(f"Transcript fetched for {video_id} (length: {len(transcript_text)} chars)")
        
        transcript_segments = []
        try:
            transcript_segments = await run_in_threadpool(get_transcript_segments, youtube_url)
            logger.debug(f"Fetched {len(transcript_segments)} transcript segments")
        except Exception as se:
            logger.warning(f"Transcript segments fetch failed: {se}")
        
        title = None
        await report_repo.set_video_meta(db, report_id, video_id, title)

        # 2) Build RAG index for this video
        try:
            await run_in_threadpool(build_index, video_id, transcript_text=transcript_text, transcript_segments=transcript_segments)
            logger.info(f"RAG index built for video {video_id}")
        except Exception as ie:
            logger.warning(f"RAG index build failed: {ie}")

        # 3) Generate artifacts using existing modules (lazy imports)
        logger.info("Generating learning artifacts...")
        from .summary_generator import summarize_text  # noqa: WPS433
        from .detail_explanation_generator import generate_notes  # noqa: WPS433
        from .mindmap_generator import generate_mindmap  # noqa: WPS433

        summary = await run_in_threadpool(summarize_text, transcript_text)
        logger.debug("Summary generated")
        
        notes = await run_in_threadpool(generate_notes, transcript_text)
        logger.debug("Notes generated")
        
        mindmap = await run_in_threadpool(generate_mindmap, transcript_text)
        logger.debug("Mind map generated")

        # 4) Export to PDF/HTML (HTML fallback stored)
        logger.info("Exporting to PDF/HTML...")
        exporter = EnhancedPDFExporter()
        
        # Helper wrapper for export_to_pdf to pass arguments cleanly
        def _export_wrapper():
            return exporter.export_to_pdf(
                video_id=video_id or "unknown",
                video_url=youtube_url,
                video_title=title,
                summary=summary,
                notes=notes,
                mindmap=mindmap,
                transcript=transcript_text,
            )
            
        output_path = await run_in_threadpool(_export_wrapper)
        logger.debug(f"Exported to: {output_path}")

        # 5) Upload to GridFS
        bucket = get_gridfs_bucket(db)
        with open(output_path, "rb") as f:
            data = f.read()
        is_html = output_path.lower().endswith(".html")
        try:
            from pathlib import Path
            filename = Path(output_path).name
        except Exception:
            filename = output_path
        
        file_id = await upload_bytes(bucket, data, filename=filename, content_type="text/html" if is_html else "application/pdf")
        logger.info(f"Artifact uploaded to GridFS (id: {file_id}, type: {'html' if is_html else 'pdf'})")

        # Store both the file IDs and the actual content in artifacts
        artifacts = {
            "html_file_id": file_id if is_html else None,
            "pdf_file_id": None if is_html else file_id,
            "summary": summary,  # Store content for PDF generation
            "notes": notes,      # Store content for PDF generation  
            "mindmap": mindmap,  # Store for future use
        }
        await report_repo.set_artifacts(db, report_id, artifacts)
        await report_repo.update_status(db, report_id, "succeeded")
        logger.info(f"Report {report_id} processed successfully with artifacts")

    except Exception as e:
        logger.exception(f"Processing failed for report {report_id}: {e}")
        await report_repo.update_status(db, report_id, "failed", error=str(e))
