from fastapi import FastAPI
from routes.auth import routes_auth


def setup(app: FastAPI):
    prefix = "/v1"
    app.include_router(routes_auth)
