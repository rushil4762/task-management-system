import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import engine, get_db
from app.routes.activities import router as activity_router
from app.routes.auth import router as auth_router
from app.routes.categories import router as category_router
from app.routes.comments import router as comment_router
from app.routes.dashboard import router as dashboard_router
from app.routes.notifications import router as notification_router
from app.routes.tags import router as tag_router
from app.routes.tasks import router as task_router
from app.routes.users import router as user_router

# Configure application logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting %s in %s environment (v%s)", settings.APP_NAME, settings.APP_ENV, settings.APP_VERSION)
    yield
    logger.info("Shutting down %s, releasing database connections", settings.APP_NAME)
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="Task and Productivity Management API using FastAPI, PostgreSQL, and SQLAlchemy.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# Enable CORS for React and other web clients
cors_kwargs = {
    "allow_origins": settings.CORS_ORIGINS,
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}

if settings.APP_ENV != "production":
    cors_kwargs["allow_origin_regex"] = r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$"

app.add_middleware(CORSMiddleware, **cors_kwargs)

# Register route modules
app.include_router(auth_router)
app.include_router(task_router)
app.include_router(category_router)
app.include_router(tag_router)
app.include_router(comment_router)
app.include_router(activity_router)
app.include_router(dashboard_router)
app.include_router(notification_router)
app.include_router(user_router)


@app.get(
    "/",
    tags=["General"],
    summary="Root service status",
)
async def root():
    return {
        "message": f"{settings.APP_NAME} is running",
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    }


@app.get(
    "/health",
    tags=["General"],
    summary="Health check endpoint",
)
async def health_check(
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    db_status = "connected"
    is_healthy = True
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error("Database health check probe failed: %s", str(exc))
        db_status = "disconnected"
        is_healthy = False
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "database": db_status,
        "environment": settings.APP_ENV,
    }