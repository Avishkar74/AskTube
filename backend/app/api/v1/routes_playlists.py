from typing import List
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from ...schemas.playlist import PlaylistCreate, PlaylistOut
from ...repositories import playlist_repo

router = APIRouter()

@router.post("/playlists", response_model=dict, summary="Create a playlist")
async def create_playlist(request: Request, payload: PlaylistCreate):
    db = request.app.state.db
    if not db:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    playlist_id = await playlist_repo.create_playlist(db, payload.youtube_url, payload.title)
    return {"id": playlist_id}

@router.get("/playlists", response_model=List[PlaylistOut], summary="List playlists")
async def list_playlists(request: Request, limit: int = 50, offset: int = 0):
    db = request.app.state.db
    if not db:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    return await playlist_repo.list_playlists(db, limit, offset)

@router.get("/playlists/{playlist_id}", response_model=PlaylistOut, summary="Get a playlist")
async def get_playlist(request: Request, playlist_id: str):
    db = request.app.state.db
    if not db:
        raise HTTPException(status_code=503, detail="Database not configured")
    
    playlist = await playlist_repo.get_playlist(db, playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return playlist
