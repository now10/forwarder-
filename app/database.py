from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from app.config import settings
import os

# Fix DATABASE_URL for Render
def get_database_url():
    database_url = settings.DATABASE_URL
    
    if not database_url:
        raise ValueError("DATABASE_URL not set")
    
    # Convert postgres:// to postgresql+psycopg2:// for async
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    
    return database_url

# Create async engine with psycopg2
engine = create_async_engine(
    get_database_url(),
    echo=settings.DEBUG,
    future=True,
    poolclass=NullPool,  # Free tier - use no pooling
    pool_pre_ping=True,  # Check connection before use
    connect_args={
        "command_timeout": 10,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 5,
        "keepalives_count": 5,
    }
)

# Create session factory
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db() -> AsyncSession:
    """
    Get database session
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
