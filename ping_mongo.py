import os, asyncio
from motor.motor_asyncio import AsyncIOMotorClient

uri = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI")
print("URI in use:", "MONGODB_URI" if os.getenv("MONGODB_URI") else "MONGO_URI")
print("URI value:", uri)

async def go():
    try:
        client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=4000)
        await client.admin.command("ping")
        print("PING OK")
    except Exception as e:
        print("PING FAIL:", e)

asyncio.run(go())
