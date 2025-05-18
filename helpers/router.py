from fastapi import FastAPI
from middleware.rbac_middleware import RBACMiddleware
from routes.auth import routes_auth
from routes.users import routes_user
from routes.feedback_user import routes_feedback_user
from helpers.config import settings


def setup(app: FastAPI):
    prefix = "/v1"
    # * RBAC Middleware
    app.add_middleware(
        RBACMiddleware,
        jwt_secret=settings.JWT_SECRET,
        allowed_paths=[
            f"{prefix}/auth/*",
            f"{prefix}/feedback-user/*",
            f"{prefix}/docs",
            f"{prefix}/redoc",
            f"{prefix}/openapi.json",
            f"{prefix}/health",
        ],
    )
    app.include_router(routes_auth, prefix=prefix)
    app.include_router(routes_auth, prefix=prefix)
    app.include_router(routes_user, prefix=prefix)
    app.include_router(routes_feedback_user, prefix=prefix)
