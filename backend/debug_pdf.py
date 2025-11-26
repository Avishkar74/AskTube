import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import get_settings

async def main():
    try:
        settings = get_settings()
        uri = settings.mongo_uri or "mongodb://localhost:27017"
        db_name = settings.mongo_db_name
        print(f"Connecting to {uri}, DB: {db_name}")
        
        client = AsyncIOMotorClient(uri)
        db = client[db_name]
        
        print("Listing reports...")
        cursor = db.reports.find().limit(5)
        async for doc in cursor:
            print(f"ID: {doc['_id']}, Video: {doc.get('video_id')}, Status: {doc.get('status')}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
