from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from app.config import settings
import logging

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=False,
    pool_size=5,
    max_overflow=10,
    connect_args={"timeout": 0.5},
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


DB_AVAILABLE: bool = False


class OfflineSession:
    """Fast in-memory mock session when PostgreSQL is offline."""
    async def execute(self, *args, **kwargs):
        raise ConnectionError("PostgreSQL database is offline — using mock demo store")

    async def commit(self):
        pass

    async def rollback(self):
        pass

    async def close(self):
        pass


def is_db_available() -> bool:
    global DB_AVAILABLE
    return DB_AVAILABLE


async def get_db():
    """Dependency: async database session with instant fallback when offline."""
    global DB_AVAILABLE
    if not DB_AVAILABLE:
        yield OfflineSession()
        return

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database: create extensions and tables."""
    global DB_AVAILABLE
    try:
        async with engine.begin() as conn:
            # Enable required extensions
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            except Exception:
                logger.warning("pgvector extension not available — RAG features will be limited")

            # Create all tables
            from app.models import Base as ModelsBase
            await conn.run_sync(ModelsBase.metadata.create_all)
        DB_AVAILABLE = True
        logger.info("Database initialized successfully")
    except Exception as e:
        DB_AVAILABLE = False
        logger.warning(f"Database connection unavailable, switching to Demo Store mode: {e}")
        raise
