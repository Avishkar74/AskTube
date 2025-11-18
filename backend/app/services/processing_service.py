from typing import Optional, Tuple
from fastapi import FastAPI

from ..repositories import report_repo
from ..db.gridfs import get_gridfs_bucket, upload_bytes
from ..core.logging import logger

# Reuse existing pipeline pieces
from transcript_extractor import get_transcript, extract_video_id, get_video_title
"""Processing service: orchestrates transcript extraction and artifact generation.

Heavy LLM-related modules are imported lazily inside the function to avoid
delaying API startup (health/status endpoints should respond quickly).
"""
from pdf_exporter import EnhancedPDFExporter


async def process_report(app: FastAPI, report_id: str, youtube_url: str, force_reindex: bool = False) -> None:
    db = app.state.db
    if db is None:
        logger.error("Database not configured; cannot process report")
        return

    await report_repo.update_status(db, report_id, "running")

    try:
        # 1) Extract transcript and basic meta
        video_id = extract_video_id(youtube_url)
        transcript_segments = get_transcript(youtube_url)
        transcript_text = " ".join([seg.get("text", "") for seg in transcript_segments])
        title = get_video_title(youtube_url)
        await report_repo.set_video_meta(db, report_id, video_id, title)

        # 2) Generate artifacts using existing modules (lazy imports)
        from summary_generator import summarize_text  # noqa: WPS433
        from detail_explanation_generator import generate_notes  # noqa: WPS433
        from mindmap_generator import generate_mindmap  # noqa: WPS433

        summary = summarize_text(transcript_text)
        notes = generate_notes(transcript_text)
        mindmap = generate_mindmap(transcript_text)

        # 3) Export to PDF/HTML (HTML fallback stored)
        exporter = EnhancedPDFExporter()
        output_path = exporter.export_to_pdf(
            video_id=video_id or "unknown",
            video_url=youtube_url,
            video_title=title,
            summary=summary,
            notes=notes,
            mindmap=mindmap,
            transcript=transcript_text,
        )

        # 4) Upload to GridFS
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

        artifacts = {
            "html_file_id": file_id if is_html else None,
            "pdf_file_id": None if is_html else file_id,
        }
        await report_repo.set_artifacts(db, report_id, artifacts)
        await report_repo.update_status(db, report_id, "succeeded")
        logger.info(f"Report {report_id} processed successfully")
    except Exception as e:
        logger.exception(f"Processing failed for report {report_id}: {e}")
        await report_repo.update_status(db, report_id, "failed", error=str(e))
