from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .db.mongo import init_mongo, close_mongo
from .api.v1.routes_health import router as health_router
from .api.v1.routes_reports import router as reports_router
from .api.v1.routes_chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_mongo(app)
    yield
    await close_mongo(app)


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="AskTube API",
        version="1.0.0",
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        docs_url=f"{settings.API_PREFIX}/docs",
        redoc_url=f"{settings.API_PREFIX}/redoc",
    )

    # CORS
    origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()] if settings.ALLOWED_ORIGINS else []
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.router.lifespan_context = lifespan

    # Routers
    app.include_router(health_router, prefix=f"{settings.API_PREFIX}/v1", tags=["health"]) 
    app.include_router(reports_router, prefix=f"{settings.API_PREFIX}/v1", tags=["reports"]) 
    app.include_router(chat_router, prefix=f"{settings.API_PREFIX}/v1", tags=["chat"]) 

    return app


app = create_app()
