from __future__ import annotations

"""Mongo repository for reports lifecycle.

Encapsulates CRUD interactions with the `reports` collection used to track the
processing job, artifacts, and minimal video metadata. All functions accept an
`AsyncIOMotorDatabase` and return plain dicts/values, keeping the API layer
simple and testable.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


def _ts() -> str:
    """Return an ISO8601 UTC timestamp with trailing 'Z'."""
    return datetime.utcnow().isoformat() + "Z"


def _oid(id_str: str) -> ObjectId:
    return ObjectId(id_str)


async def insert_report(db: Any, youtube_url: str, video_id: Optional[str] = None) -> str:
    """Insert a new report document and return its stringified ObjectId."""
    doc = {
        "youtube_url": youtube_url,
        "video_id": video_id,
        "status": "queued",
        "created_at": _ts(),
        "updated_at": _ts(),
        "artifacts": {},
    }
    res = await db["reports"].insert_one(doc)
    return str(res.inserted_id)


async def update_status(db: Any, report_id: str, status: str, error: Optional[str] = None) -> None:
    """Update the status (and optional error) for a report."""
    updates: Dict[str, Any] = {"status": status, "updated_at": _ts()}
    if error:
        updates["error"] = error
    await db["reports"].update_one({"_id": _oid(report_id)}, {"$set": updates})


async def set_artifacts(db: Any, report_id: str, artifacts: Dict[str, Any]) -> None:
    """Set artifact references (e.g., GridFS IDs) for a report."""
    await db["reports"].update_one({"_id": _oid(report_id)}, {"$set": {"artifacts": artifacts, "updated_at": _ts()}})


async def set_video_meta(db: Any, report_id: str, video_id: Optional[str], title: Optional[str]) -> None:
    """Persist minimal video metadata derived during processing."""
    await db["reports"].update_one({"_id": _oid(report_id)}, {"$set": {"video_id": video_id, "title": title, "updated_at": _ts()}})


async def get_by_id(db: Any, report_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a report by id and stringify its `_id` field."""
    doc = await db["reports"].find_one({"_id": _oid(report_id)})
    if not doc:
        return None
    doc["_id"] = str(doc["_id"])  # stringify
    return doc


async def list_reports(db: Any, video_id: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """List reports with optional filtering and pagination.

    Sorted by `created_at` descending. Offsets are clamped to non-negative.
    """
    query: Dict[str, Any] = {}
    if video_id:
        query["video_id"] = video_id
    cursor = db["reports"].find(query).sort("created_at", -1).skip(max(0, int(offset))).limit(int(limit))
    items: List[Dict[str, Any]] = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])  # stringify
        items.append(doc)
    return items


async def count_reports(db: Any, video_id: Optional[str] = None) -> int:
    """Return total number of reports matching the optional filter."""
    query: Dict[str, Any] = {}
    if video_id:
        query["video_id"] = video_id
    return await db["reports"].count_documents(query)
