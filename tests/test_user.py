import pytest
from httpx import AsyncClient

BASE_URL = "http://127.0.0.1:8000"


#test for user registeration and login
@pytest.mark.asyncio
async def test_register_and_login():
    async with AsyncClient(base_url=BASE_URL) as ac:
        reg_data = {
            "username": "testuser1",
            "first_name": "Test",
            "last_name": "User",
            "email": "testuser1@example.com",
            "password": "strongpassword123"
        }
        response = await ac.post("/auth/register", json=reg_data)

    assert response.status_code == 200, response.text
    token_data = response.json()
    assert isinstance(token_data.get("access_token"), str)
    assert isinstance(token_data.get("token_type"), str)

    # login with same user
    async with AsyncClient(base_url=BASE_URL) as ac:
        login_data = {
            "username": reg_data["username"],
            "password": reg_data["password"]
        }
        response = await ac.post("/auth/login", json=login_data)

    assert response.status_code == 200, response.text
    token_data = response.json()
    assert isinstance(token_data.get("access_token"), str)
    assert isinstance(token_data.get("token_type"), str)

@pytest.mark.asyncio
async def test_register_existing_username():
    # registering again with same username
    async with AsyncClient(base_url=BASE_URL) as ac:
        reg_data = {
            "username": "testuser1",  # already exists
            "first_name": "Another",
            "last_name": "User",
            "email": "anotheremail@example.com",
            "password": "strongpassword123"
        }
        response = await ac.post("/auth/register", json=reg_data)

    assert response.status_code == 400, response.text

@pytest.mark.asyncio
async def test_register_existing_email():
    # try registering again with same email
    async with AsyncClient(base_url=BASE_URL) as ac:
        reg_data = {
            "username": "uniqueusername",
            "first_name": "Another",
            "last_name": "User",
            "email": "testuser1@example.com",  # already used
            "password": "strongpassword123"
        }
        response = await ac.post("/auth/register", json=reg_data)

    assert response.status_code == 400, response.text

@pytest.mark.asyncio
async def test_login_wrong_username():
    async with AsyncClient(base_url=BASE_URL) as ac:
        login_data = {
            "username": "nonexistentuser",
            "password": "strongpassword123"
        }
        response = await ac.post("/auth/login", json=login_data)

    assert response.status_code == 400, response.text

@pytest.mark.asyncio
async def test_login_wrong_password():
    async with AsyncClient(base_url=BASE_URL) as ac:
        login_data = {
            "username": "testuser1",
            "password": "wrongpassword"
        }
        response = await ac.post("/auth/login", json=login_data)

    assert response.status_code == 400, response.text
