from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from gridfs import NoFile
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from bson import ObjectId


def get_gridfs_bucket(db: Optional[AsyncIOMotorDatabase]) -> Optional[AsyncIOMotorGridFSBucket]:
    if db is None:
        return None
    return AsyncIOMotorGridFSBucket(db)


async def upload_bytes(bucket: AsyncIOMotorGridFSBucket, data: bytes, filename: str, content_type: str = "text/html") -> str:
    file_id = await bucket.upload_from_stream(filename, data, metadata={"content_type": content_type})
    return str(file_id)


async def download_bytes(bucket: AsyncIOMotorGridFSBucket, file_id) -> bytes:
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
