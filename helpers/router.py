from fastapi import FastAPI
from middleware.rbac_middleware import RBACMiddleware
from routes.auth import routes_auth
from routes.users import routes_user
from routes.feedback_user import routes_feedback_user
from routes.district import routes_district
from routes.villages import routes_village
from routes.reports import routes_report
from helpers.config import settings


def setup(app: FastAPI):
    prefix = "/v1"
    app.include_router(routes_auth, prefix=prefix)
    app.include_router(routes_auth, prefix=prefix)
    app.include_router(routes_user, prefix=prefix)
    app.include_router(routes_report, prefix=prefix)
    app.include_router(routes_feedback_user, prefix=prefix)
    app.include_router(routes_district, prefix=prefix)
    app.include_router(routes_village, prefix=prefix)
