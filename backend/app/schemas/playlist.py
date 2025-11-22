from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

class PlaylistBase(BaseModel):
    youtube_url: str
    title: Optional[str] = None

class PlaylistCreate(PlaylistBase):
    pass

class PlaylistInDB(PlaylistBase):
    id: str
    video_ids: List[str] = []
    created_at: datetime
    updated_at: datetime

class PlaylistOut(PlaylistInDB):
    pass
