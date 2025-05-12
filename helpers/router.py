from fastapi import FastAPI

from routes.my_model import router as router_my_model
from routes.interview import routes_interview
from routes.auth import routes_auth


def setup(app: FastAPI):
    prefix = "/v1"
    app.include_router(router_my_model, prefix=prefix)
    app.include_router(routes_auth)
