import os
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///database.db"  # for dev
)

engine = create_async_engine(DATABASE_URL, echo=True)


AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    expire_on_commit=False
)



async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

# Dependency
async def get_session() -> AsyncSession:  # type: ignore
    async with AsyncSessionLocal() as session:
        yield session # type: ignore
