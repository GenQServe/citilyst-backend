import sys
from fastapi import FastAPI, Request
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import close_all_sessions
import logging
import uvicorn
from helpers import cors, log, rate_limiter, static, router
from helpers.scheduler import setup as scheduler_setup
from helpers.db import db_connection

# Setup logging
log.setup()

app = FastAPI(
    title="Citilyst - API Documentation",
    version="0.1.0",
    description="Documentation API for Rekrut AI",
)

is_production = "--production" in sys.argv
mainport = (
    8000 if "--port" not in sys.argv else int(sys.argv[sys.argv.index("--port") + 1])
)
is_development = not is_production

# Setup Middleware
rate_limiter.setup(app)
cors.setup(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     logging.info("🚀 Starting up: Initializing Database Connection")
#     await db_connection.init()
#     yield
#     logging.info("🛑 Shutting down: Closing Database Connection")
#     close_all_sessions()
#     await db_connection.close()


# Setup Routes & Static Files
router.setup(app)
static.setup(app)

# Scheduler
scheduler_setup(app)

# Import scheduler jobs
import jobs

_ = jobs.__name__


def main():
    print("[RUN MODE]:", "PRODUCTION" if is_production else "DEVELOPMENT")
    uvicorn.run("main:app", host="0.0.0.0", port=mainport, reload=is_development)


if __name__ == "__main__":
    main()
