import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from urllib.parse import urlparse
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv()

Base = declarative_base()
tmpPostgres = urlparse(os.getenv("DATABASE_URL"))


class Connection:
    def __init__(self):
        self.url = os.getenv("DATABASE_URL")
        self.engine = create_async_engine(
            f"postgresql+asyncpg://{tmpPostgres.username}:{tmpPostgres.password}@{tmpPostgres.hostname}{tmpPostgres.path}?ssl=require",
            pool_size=20,  # Set a reasonable pool size
            max_overflow=10,  # Allow some overflow connections
            pool_timeout=30,  # Connection timeout in seconds
            pool_recycle=1800,  # Recycle connections every 30 minutes
            pool_pre_ping=True,  # Check connection validity before using
            echo=False,  # Set to True for debugging SQL queries
        )

        self.SessionLocal = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,  # Don't auto-flush for better control
        )

    @asynccontextmanager
    async def get_db_session(self):
        """Get a database session as an async context manager"""
        session = self.SessionLocal()
        try:
            yield session
        finally:
            await session.close()

    async def get_db(self):
        """Get a database session as a FastAPI dependency"""
        async with self.SessionLocal() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()

    async def close(self):
        """Close all connections in the engine's connection pool"""
        await self.engine.dispose()


# Singleton instance
db_connection = Connection()
