import os
import logging
import secrets
import sys
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from contextlib import asynccontextmanager
from urllib.parse import urlparse

load_dotenv()

Base = declarative_base()

is_production = (
    os.getenv("ENVIRONMENT", "development").lower() == "production"
    or "--production" in sys.argv
)


def get_database_url():
    raw_url = os.getenv("DATABASE_URL")

    if not raw_url:
        print("DATABASE_URL tidak ditemukan di environment variables.")
        return "sqlite+aiosqlite:///./test.db"

    if raw_url.startswith("postgresql://") and not raw_url.startswith(
        "postgresql+asyncpg://"
    ):
        try:
            parsed = urlparse(raw_url)
            return f"postgresql+asyncpg://{parsed.username}:{parsed.password}@{parsed.hostname}{parsed.path}"
        except Exception as e:
            print(f"Error parsing DATABASE_URL: {e}")
            return "sqlite+aiosqlite:///./test.db"
    return raw_url


DATABASE_URL = get_database_url()
logging.info(
    f"Using database: {DATABASE_URL.split('@')[0].split('://')[0]}://*****@*****"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    connect_args={"command_timeout": 10},  #
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def init_models():
    """Initialize database tables."""
    try:
        print("Creating database tables if not exist...")

        from models.users import User

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables initialized successfully")
    except Exception as e:
        print(f"Error initializing database tables: {e}")
        raise


async def get_db():
    """Get database session for FastAPI dependency injection."""
    session = AsyncSessionLocal()
    try:
        yield session
    except Exception as e:
        print(f"Database session error: {e}")
        await session.rollback()
        raise
    finally:
        await session.close()


class Connection:
    """Database connection manager."""

    def __init__(self):
        self.engine = engine
        self.SessionLocal = AsyncSessionLocal

    async def init(self):
        """Initialize database tables."""
        await init_models()

    # Fungsi alternatif jika butuh session di luar request handler
    async def get_session(self):
        """Get a new session outside of request handlers."""
        session = self.SessionLocal()
        try:
            return session
        except Exception as e:
            logging.error(f"Error creating session: {e}")
            await session.close()
            raise

    @asynccontextmanager
    async def get_db_session(self):
        session = self.SessionLocal()
        try:
            yield session
        except Exception as e:
            logging.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

    async def close(self):
        """Close database connection."""
        print("Closing database connection...")
        await self.engine.dispose()
        print("Database connection closed")


db_connection = Connection()
