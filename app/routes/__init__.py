from app.routes.auth import router as auth_router
from app.routes.tasks import router as task_router

__all__ = ["task_router", "auth_router"]
