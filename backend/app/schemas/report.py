from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ReportIn(BaseModel):
    youtube_url: str
    force_reindex: bool = False


class ReportMeta(BaseModel):
    id: str = Field(alias="_id")
    youtube_url: str
    video_id: Optional[str] = None
    title: Optional[str] = None
    status: str
    created_at: str
    updated_at: str
    artifacts: Optional[Dict[str, Any]] = None


class ReportOut(BaseModel):
    report_id: str
