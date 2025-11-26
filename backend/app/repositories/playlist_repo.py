from datetime import datetime, timezone
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

COLLECTION = "playlists"

async def create_playlist(db: AsyncIOMotorDatabase, youtube_url: str, title: str = None) -> str:
    doc = {
        "youtube_url": youtube_url,
        "title": title,
        "video_ids": [],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    result = await db[COLLECTION].insert_one(doc)
    return str(result.inserted_id)

async def get_playlist(db: AsyncIOMotorDatabase, playlist_id: str) -> Optional[dict]:
    try:
        oid = ObjectId(playlist_id)
    except:
        return None
    doc = await db[COLLECTION].find_one({"_id": oid})
    if doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    return doc

async def list_playlists(db: AsyncIOMotorDatabase, limit: int = 50, offset: int = 0) -> List[dict]:
    cursor = db[COLLECTION].find().sort("created_at", -1).skip(offset).limit(limit)
    items = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        items.append(doc)
    return items

async def add_video_to_playlist(db: AsyncIOMotorDatabase, playlist_id: str, video_id: str):
    try:
        oid = ObjectId(playlist_id)
    except:
        return False
    
    await db[COLLECTION].update_one(
        {"_id": oid},
        {
            "$addToSet": {"video_ids": video_id},
            "$set": {"updated_at": datetime.now(timezone.utc)}
        }
    )
    return True
