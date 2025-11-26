"""Config endpoint to help frontends discover runtime flags.

Exposes selected non-sensitive settings so the frontend can adapt behavior
without hardcoding values. Avoids leaking secrets.
"""

from fastapi import APIRouter

from ...core.config import get_settings


router = APIRouter()


@router.get("/config", summary="Frontend config", response_model=dict)
async def get_config():
    """Return non-sensitive runtime configuration for the frontend.

    Includes:
    - api_prefix: Mount prefix for API routes
    - use_rag: Default RAG feature flag
    - allowed_origins: CORS origins (comma-separated string as configured)
    - exposed_headers: Response headers exposed to browsers (for tracing)
    - version: API version string
    """
    s = get_settings()
    return {
        "api_prefix": s.API_PREFIX,
        "use_rag": s.USE_RAG,
        "allowed_origins": s.ALLOWED_ORIGINS,
        "exposed_headers": ["X-Request-ID"],
        "version": "v1",
    }
