from fastapi import FastAPI
from middleware.rbac_middleware import RBACMiddleware
from routes.auth import routes_auth
from routes.users import routes_user
from helpers.config import settings


def setup(app: FastAPI):
    prefix = "/v1"
    # * RBAC Middleware
    app.add_middleware(
        RBACMiddleware,
        jwt_secret=settings.JWT_SECRET or "",
        allowed_paths=[
            f"{prefix}/auth/*",
            f"{prefix}/docs",
            f"{prefix}/redoc",
            f"{prefix}/openapi.json",
            f"{prefix}/health",
        ],
    )
    app.include_router(routes_auth, prefix=prefix)
    app.include_router(routes_auth, prefix=prefix)
    app.include_router(routes_user, prefix=prefix)
