from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from gridfs import NoFile
from motor.motor_asyncio import AsyncIOMotorGridFSBucket


def get_gridfs_bucket(db: Optional[AsyncIOMotorDatabase]) -> Optional[AsyncIOMotorGridFSBucket]:
    if db is None:
        return None
    return AsyncIOMotorGridFSBucket(db)


async def upload_bytes(bucket: AsyncIOMotorGridFSBucket, data: bytes, filename: str, content_type: str = "text/html") -> str:
    file_id = await bucket.upload_from_stream(filename, data, metadata={"content_type": content_type})
    return str(file_id)


async def download_bytes(bucket: AsyncIOMotorGridFSBucket, file_id) -> bytes:
    # file_id should be ObjectId or str; motor accepts str in open_download_stream
    try:
        stream = await bucket.open_download_stream(file_id)
    except NoFile:
        raise FileNotFoundError("File not found in GridFS")
    chunks = bytearray()
    while True:
        data = await stream.read()
        if not data:
            break
        chunks.extend(data)
    return bytes(chunks)
