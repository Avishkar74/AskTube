"""Pydantic models for report API payloads and metadata."""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ReportIn(BaseModel):
    """Inbound payload to initiate processing for a YouTube URL."""
    youtube_url: str
    force_reindex: bool = False


class ReportMeta(BaseModel):
    """Stored representation of a processing job (reports collection)."""
    id: str = Field(alias="_id")
    youtube_url: str
    video_id: Optional[str] = None
    title: Optional[str] = None
    status: str
    created_at: str
    updated_at: str
    artifacts: Optional[Dict[str, Any]] = None


class ReportOut(BaseModel):
    """Response containing an ID for the created processing job."""
    report_id: str
