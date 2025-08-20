import os

import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlmodel import SQLModel

from app.core.database import get_session
from app.main import app

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
TEST_DATABASE_URL = os.environ["DATABASE_URL"]

# creating test_engine for testing
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)

# testing async session
TestAsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    test_engine, expire_on_commit=False
)


# test initialize db
@pytest_asyncio.fixture(scope="session")
async def initialized_db() -> None:  # type: ignore
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield  # type: ignore
    # drop tables after tests
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


# override get_session dependency for test
async def override_get_session() -> AsyncSession:  # type: ignore
    async with TestAsyncSessionLocal() as session:
        try:
            yield session  # type: ignore
        finally:
            await session.close()


# create test_app with overrided dependency
@pytest_asyncio.fixture(scope="session")
async def test_app(initialized_db):
    app.dependency_overrides[get_session] = override_get_session
    yield app


# async client for handling request and Lifespan Manager
@pytest_asyncio.fixture()
async def client(test_app):
    os.environ["TESTING"] = "1"
    async with LifespanManager(test_app):
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
