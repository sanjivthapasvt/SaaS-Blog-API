import os
import asyncio
import pytest
import pytest_asyncio

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.main import app
from app.core.database import get_session


TEST_DATABASE_URL = os.environ["DATABASE_URL"]
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestAsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    test_engine, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="session")
async def initialized_db() -> None: # type: ignore
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield # type: ignore
    # drop tables after tests
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


async def override_get_session() -> AsyncSession: # type: ignore
    async with TestAsyncSessionLocal() as session:
        try:
            yield session # type: ignore
        finally:
            await session.close()


@pytest_asyncio.fixture(scope="session")
async def test_app(initialized_db):
    app.dependency_overrides[get_session] = override_get_session
    async with LifespanManager(app):
        yield app


@pytest_asyncio.fixture()
async def client(test_app):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


