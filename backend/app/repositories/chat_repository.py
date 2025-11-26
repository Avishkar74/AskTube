from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..schemas.chat_history import ChatMessage, ChatHistory
from ..core.logging import logger

COLLECTION_NAME = "chat_history"

async def save_message(db: AsyncIOMotorDatabase, video_id: str, message: ChatMessage) -> None:
    """Append a message to the chat history for a video."""
    try:
        await db[COLLECTION_NAME].update_one(
            {"video_id": video_id},
            {"$push": {"messages": message.model_dump()}},
            upsert=True
        )
    except Exception as e:
        logger.error(f"Failed to save chat message for video {video_id}: {e}")

async def get_history(db: AsyncIOMotorDatabase, video_id: str) -> List[ChatMessage]:
    """Retrieve chat history for a video."""
    try:
        doc = await db[COLLECTION_NAME].find_one({"video_id": video_id})
        if doc and "messages" in doc:
            return [ChatMessage(**msg) for msg in doc["messages"]]
        return []
    except Exception as e:
        logger.error(f"Failed to retrieve chat history for video {video_id}: {e}")
        return []
