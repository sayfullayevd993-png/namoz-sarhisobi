from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings, BASE_DIR
from app.database.base import Base

db_url = settings.async_database_url

if db_url.startswith("sqlite"):
    # Agar SQLite bo'lsa, fayl joylashgan papka mavjudligini ta'minlash
    # sqlite+aiosqlite:///path/to/db
    raw_path = db_url.replace("sqlite+aiosqlite:///", "")
    db_file_path = Path(raw_path)
    if not db_file_path.is_absolute():
        db_file_path = BASE_DIR / db_file_path
    db_file_path.parent.mkdir(parents=True, exist_ok=True)

    engine = create_async_engine(
        db_url,
        echo=False,
        future=True
    )
else:
    # PostgreSQL (Railway) uchun ulanishlar puli (pool) parametrlari
    engine = create_async_engine(
        db_url,
        echo=False,
        future=True,
        pool_size=10,
        max_overflow=20,
        pool_recycle=300,
        pool_pre_ping=True
    )

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with async_session_maker() as session:
        yield session
