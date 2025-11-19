"""Helpers for working with Mongo GridFS via Motor.

This module exposes minimal helper functions used by the processing pipeline to
upload and download binary artifacts (HTML/PDF) to/from MongoDB GridFS.
"""
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from gridfs import NoFile
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from bson import ObjectId


def get_gridfs_bucket(db: Optional[AsyncIOMotorDatabase]) -> Optional[AsyncIOMotorGridFSBucket]:
    """Create an `AsyncIOMotorGridFSBucket` from a database handle.

    Returns None if the provided `db` is None, allowing callers to short-circuit
    in environments where Mongo is not configured.
    """
    if db is None:
        return None
    return AsyncIOMotorGridFSBucket(db)


async def upload_bytes(bucket: AsyncIOMotorGridFSBucket, data: bytes, filename: str, content_type: str = "text/html") -> str:
    """Upload `data` as a new GridFS file and return its ID as a string.

    Metadata includes a `content_type` hint (e.g., `text/html` or `application/pdf`).
    """
    file_id = await bucket.upload_from_stream(filename, data, metadata={"content_type": content_type})
    return str(file_id)


async def download_bytes(bucket: AsyncIOMotorGridFSBucket, file_id) -> bytes:
    """Download a GridFS file by id, accepting either `str` or `ObjectId`.

    Converts string IDs to `ObjectId` when possible; otherwise lets Motor try
    the raw value. Raises `FileNotFoundError` when the file does not exist.
    Returns the full file content as bytes.
    """
    # Accept either ObjectId or str and normalize to ObjectId when possible
    _fid = file_id
    if isinstance(file_id, str):
        try:
            _fid = ObjectId(file_id)
        except Exception:
            # Fallback: let motor try the provided value
            _fid = file_id
    try:
        stream = await bucket.open_download_stream(_fid)
    except NoFile:
        raise FileNotFoundError("File not found in GridFS")
    chunks = bytearray()
    while True:
        data = await stream.read()
        if not data:
            break
        chunks.extend(data)
    return bytes(chunks)
