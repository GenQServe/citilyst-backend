import sys
import os
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
from helpers.config import settings
from middleware.rbac_middleware import RBACMiddleware

# Setup logging
log.setup()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logging.info("Starting application...")
        logging.info("Initializing database connection & tables")
        await db_connection.init()
        logging.info("Database initialized successfully")
        yield
    except Exception as e:
        logging.error(f"Error during startup: {e}")
        raise
    finally:
        logging.info("Shutting down application...")
        try:
            close_all_sessions()
            await db_connection.close()
            logging.info("Application shutdown complete")
        except Exception as e:
            logging.error(f"Error during shutdown: {e}")


app = FastAPI(
    title="Citilyst - API Documentation",
    version="0.1.0",
    description="Documentation API for Citilyst Application",
    lifespan=lifespan,
)

mainport = int(os.getenv("PORT", "8000"))
if "--port" in sys.argv:
    try:
        mainport = int(sys.argv[sys.argv.index("--port") + 1])
    except (IndexError, ValueError):
        pass

# Setup Middleware
rate_limiter.setup(app)
cors.setup(app)

# allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
allowed_origins = [
    "http://localhost:5173",
    "https://citilyst.rekrutgenai.com",
]

prefix = "/v1"

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

# Setup Routes & Static Files
router.setup(app)
static.setup(app)

# Scheduler
scheduler_setup(app)

# Import scheduler jobs
import jobs

_ = jobs.__name__


def main():
    print(
        f"[ENV] Running in {'PRODUCTION' if settings.is_production else 'DEVELOPMENT'} mode"
    )
    print(f"[PORT] Listening on port {mainport}")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=mainport,
        reload=settings.is_development,
        log_level="info",
    )


if __name__ == "__main__":
    main()
