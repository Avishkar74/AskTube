"""Course schemas for playlist/course support."""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class VideoInCourse(BaseModel):
    """Represents a video within a course/playlist."""
    video_id: str
    title: str
    duration: int  # seconds
    thumbnail: str
    order: int  # position in playlist
    report_id: Optional[str] = None  # Reference to Report document


class CourseIn(BaseModel):
    """Input schema for creating a course."""
    playlist_url: str
    force_reindex: bool = False


class CourseOut(BaseModel):
    """Output schema for course data."""
    id: str = Field(alias="_id")
    playlist_id: str
    title: str
    description: Optional[str] = None
    thumbnail: Optional[str] = None
    channel_name: Optional[str] = None
    video_count: int
    videos: List[VideoInCourse]
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
