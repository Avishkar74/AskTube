from datetime import datetime
from typing import Optional, Dict, Any, List
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


def _ts() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _oid(id_str: str) -> ObjectId:
    return ObjectId(id_str)


async def insert_report(db: AsyncIOMotorDatabase, youtube_url: str) -> str:
    doc = {
        "youtube_url": youtube_url,
        "status": "queued",
        "created_at": _ts(),
        "updated_at": _ts(),
        "artifacts": {},
    }
    res = await db["reports"].insert_one(doc)
    return str(res.inserted_id)


async def update_status(db: AsyncIOMotorDatabase, report_id: str, status: str, error: Optional[str] = None) -> None:
    updates: Dict[str, Any] = {"status": status, "updated_at": _ts()}
    if error:
        updates["error"] = error
    await db["reports"].update_one({"_id": _oid(report_id)}, {"$set": updates})


async def set_artifacts(db: AsyncIOMotorDatabase, report_id: str, artifacts: Dict[str, Any]) -> None:
    await db["reports"].update_one({"_id": _oid(report_id)}, {"$set": {"artifacts": artifacts, "updated_at": _ts()}})


async def set_video_meta(db: AsyncIOMotorDatabase, report_id: str, video_id: Optional[str], title: Optional[str]) -> None:
    await db["reports"].update_one({"_id": _oid(report_id)}, {"$set": {"video_id": video_id, "title": title, "updated_at": _ts()}})


async def get_by_id(db: AsyncIOMotorDatabase, report_id: str) -> Optional[Dict[str, Any]]:
    doc = await db["reports"].find_one({"_id": _oid(report_id)})
    if not doc:
        return None
    doc["_id"] = str(doc["_id"])  # stringify
    return doc


async def list_reports(db: AsyncIOMotorDatabase, video_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    query: Dict[str, Any] = {}
    if video_id:
        query["video_id"] = video_id
    cursor = db["reports"].find(query).sort("created_at", -1).limit(limit)
    items: List[Dict[str, Any]] = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])  # stringify
        items.append(doc)
    return items
