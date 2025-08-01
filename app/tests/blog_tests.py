from fastapi.testclient import TestClient
from main import app
from auth.schemas import Token
client = TestClient(app)

def test_login():
    response = client.get("/auth/login")
    assert response.status_code == 200
    assert response.json() == Token