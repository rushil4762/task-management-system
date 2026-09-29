from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine
from app.routes.activities import router as activity_router
from app.routes.auth import router as auth_router
from app.routes.categories import router as category_router
from app.routes.comments import router as comment_router
from app.routes.dashboard import router as dashboard_router
from app.routes.notifications import router as notification_router
from app.routes.tags import router as tag_router

from app.routes.tasks import router as task_router




@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup actions
    yield
    # Graceful shutdown: release database connection pool
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="Task and Productivity Management API using FastAPI, PostgreSQL, and SQLAlchemy.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# Enable CORS for React and other web clients
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Register route modules
app.include_router(auth_router)
app.include_router(task_router)
app.include_router(category_router)
app.include_router(tag_router)
app.include_router(comment_router)
app.include_router(activity_router)
app.include_router(dashboard_router)
app.include_router(notification_router)






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
async def health_check():
    return {
        "status": "healthy",
    }