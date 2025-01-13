import pytest
from fastapi.testclient import TestClient
from app.api.routes import router  # Import router s endpointy
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)

client = TestClient(app)

def test_login_success():
    response = client.post(
        "/login",
        json={"username": "example_user", "password": "example_password"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["customer_id"] == 1
    assert data["name"] == "example_user"
    assert data["company"] == "Example Corp"
    assert data["monthly_tokens"] == 100
    assert data["remaining_tokens"] == 50

def test_login_invalid_password():
    response = client.post(
        "/login",
        json={"username": "example_user", "password": "wrong_password"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid password"

def test_login_user_not_found():
    response = client.post(
        "/login",
        json={"username": "nonexistent_user", "password": "example_password"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "User not found or inactive"
