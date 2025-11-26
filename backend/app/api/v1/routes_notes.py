import os
import socket
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import List
import shutil
from pathlib import Path

router = APIRouter()

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def get_local_ip():
    try:
        # Connect to an external server (doesn't actually send data) to get the local IP used for routing
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

@router.get("/notes/ip")
async def get_ip():
    return {"ip": get_local_ip()}

@router.post("/notes/{video_id}/upload")
async def upload_note(video_id: str, file: UploadFile = File(...)):
    video_upload_dir = UPLOAD_DIR / video_id
    video_upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = video_upload_dir / file.filename
    
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")
        
    return {"filename": file.filename, "url": f"/static/uploads/{video_id}/{file.filename}"}

@router.get("/notes/{video_id}")
async def list_notes(video_id: str):
    video_upload_dir = UPLOAD_DIR / video_id
    if not video_upload_dir.exists():
        return []
        
    files = []
    for file_path in video_upload_dir.glob("*"):
        if file_path.is_file():
            files.append({
                "filename": file_path.name,
                "url": f"/static/uploads/{video_id}/{file_path.name}"
            })
            
    return files
