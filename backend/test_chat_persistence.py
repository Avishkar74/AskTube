import asyncio
import sys
import os

# Add current directory to sys.path
sys.path.append(os.getcwd())

from app.schemas.chat_history import ChatMessage
from app.repositories.chat_repository import save_message, get_history
from app.db.mongo import _attempt_connect
from app.core.config import get_settings
import time

async def test():
    print("Testing imports...")
    print("ChatMessage imported:", ChatMessage)
    
    msg = ChatMessage(
        id="test_id",
        role="user",
        content="hello",
        timestamp=time.time()
    )
    print("ChatMessage created:", msg)
    
    settings = get_settings()
    if not settings.mongo_uri:
        print("No Mongo URI, skipping DB test")
        return

    print("Connecting to Mongo...")
    client = await _attempt_connect(settings.mongo_uri)
    if not client:
        print("Failed to connect to Mongo")
        return
        
    db = client[settings.mongo_db_name]
    print("Connected to DB:", db.name)
    
    print("Testing save_message...")
    await save_message(db, "test_video", msg)
    print("Message saved.")
    
    print("Testing get_history...")
    history = await get_history(db, "test_video")
    print("History retrieved:", history)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(test())
