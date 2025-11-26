"""Health and readiness endpoints.

This module exposes lightweight probes used by load balancers and dev tools:

- GET /health: Liveness/health check. Reports current UTC timestamp, basic
    Mongo connection status, and last connection error if present. This should
    return quickly even when background services are busy. A "degraded" status
    indicates the API is up but not fully connected to Mongo.
- GET /ready: Readiness check. Verifies Mongo connectivity and performs a
    lightweight list of collection names to ensure the database handle works.
    Returns {"status": "ready"} only when the app can serve traffic that
    depends on Mongo.
"""

from fastapi import APIRouter, Request
from datetime import datetime, timezone

router = APIRouter()


@router.get("/health")
async def health(request: Request):
    """Return a simple health status with Mongo connection details.

    - status: "ok" when Mongo is connected, otherwise "degraded".
    - details.timestamp: Current UTC time (ISO8601) for quick diagnostics.
    - details.mongo_connected: Boolean indicating Mongo connectivity.
    - details.mongo_error: Optional last connection error string.
    """
    db = getattr(request.app.state, "db", None)
    mongo_connected = getattr(request.app.state, "mongo_connected", False)
    mongo_error = getattr(request.app.state, "mongo_error", None)
    details = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mongo_connected": mongo_connected,
    }
    if mongo_error:
        details["mongo_error"] = mongo_error
    status = "ok" if mongo_connected else "degraded"
    return {"status": status, "details": details}


@router.get("/ready")
async def ready(request: Request):
    """Return readiness status once Mongo is usable by request handlers.

    This performs a very small database operation (`list_collection_names`) to
    ensure the connection is ready to serve requests that depend on Mongo.
    """
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
