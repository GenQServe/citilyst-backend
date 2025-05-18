from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def setup(app: FastAPI):
    allowed_origins = [
        "http://localhost:5173",
        "https://citilyst.rekrutgenai.com",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
