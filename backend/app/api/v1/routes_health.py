from fastapi import APIRouter, Request
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def health(request: Request):
    db = getattr(request.app.state, "db", None)
    mongo_connected = getattr(request.app.state, "mongo_connected", False)
    mongo_error = getattr(request.app.state, "mongo_error", None)
    details = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "mongo_connected": mongo_connected,
    }
    if mongo_error:
        details["mongo_error"] = mongo_error
    status = "ok" if mongo_connected else "degraded"
    return {"status": status, "details": details}


@router.get("/ready")
async def ready(request: Request):
    # Readiness implies DB connected and basic collections accessible (optional lightweight check)
    mongo_connected = getattr(request.app.state, "mongo_connected", False)
    if not mongo_connected:
        return {"status": "not-ready", "reason": getattr(request.app.state, "mongo_error", "mongo not connected")}
    try:
        db = getattr(request.app.state, "db", None)
        if db is None:
            return {"status": "not-ready", "reason": "db handle missing"}
        # simple listCollections command
        await db.list_collection_names()
        return {"status": "ready"}
    except Exception as e:
        return {"status": "not-ready", "reason": str(e)}
