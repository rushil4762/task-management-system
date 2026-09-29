from app.routes.activities import router as activity_router
from app.routes.auth import router as auth_router
from app.routes.categories import router as category_router
from app.routes.comments import router as comment_router
from app.routes.dashboard import router as dashboard_router
from app.routes.tags import router as tag_router
from app.routes.tasks import router as task_router

__all__ = [
    "task_router",
    "auth_router",
    "category_router",
    "tag_router",
    "comment_router",
    "activity_router",
    "dashboard_router",
]

