from uuid import uuid4
from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def unique_value(prefix: str) -> str:
    # Creates unique values so tests can be repeated
    return f"{prefix}_{datetime.now().timestamp()}".replace(".", "_")


def auth_headers(token: str) -> dict:
    # Sends JWT token in Authorization header
    return {"Authorization": f"Bearer {token}"}


def login(email: str, password: str) -> str:
    # Helper to log in and return token
    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200
    return response.json()["access_token"]


def test_login_wrong_password_fails():
    response = client.post(
        "/auth/login",
        json={
            "email": "cod@example.com",
            "password": "wrong_password",
        },
    )

    assert response.status_code == 401


def test_users_me_without_token_fails():
    response = client.get("/users/me")

    # Depending on HTTPBearer config, this may be 401 or 403
    assert response.status_code in [401, 403]


def test_create_duplicate_role_fails():
    token = login("cod@example.com", "123456")

    role_name = unique_value("duplicate_test_role")

    # First creation should work
    first_response = client.post(
        "/roles/",
        headers=auth_headers(token),
        json={
            "name": role_name,
            "description": "First role creation",
        },
    )

    assert first_response.status_code == 201

    # Second creation with same name should fail
    second_response = client.post(
        "/roles/",
        headers=auth_headers(token),
        json={
            "name": role_name,
            "description": "Duplicate role creation",
        },
    )

    assert second_response.status_code in [400, 409]


def test_create_duplicate_client_company_name_fails():
    token = login("cod@example.com", "123456")

    company_name = unique_value("duplicate_client")

    # First client should be created
    first_response = client.post(
        "/clients/",
        headers=auth_headers(token),
        json={
            "company_name": company_name,
            "email": f"{company_name}@example.com",
            "phone_1": "0919000001",
            "phone_2": "0929000001",
            "address": "Tripoli",
        },
    )

    assert first_response.status_code == 201

    # Second client with same company_name should fail
    second_response = client.post(
        "/clients/",
        headers=auth_headers(token),
        json={
            "company_name": company_name,
            "email": f"{company_name}_2@example.com",
            "phone_1": "0919000002",
            "phone_2": "0929000002",
            "address": "Tripoli",
        },
    )

    assert second_response.status_code in [400, 409]


def test_create_contact_with_invalid_company_id_fails():
    token = login("cod@example.com", "123456")

    response = client.post(
        "/contacts/",
        headers=auth_headers(token),
        json={
            "company_type": "client",
            "company_id": str(uuid4()),
            "fullname": "Invalid Company Contact",
            "position": "Manager",
            "email": "invalid.company.contact@example.com",
            "phone_1": "0959000001",
            "phone_2": "0969000001",
        },
    )

    assert response.status_code == 400


def test_sales_manager_cannot_create_user():
    sales_manager_token = login("sales.manager@example.com", "123456")

    username = unique_value("blocked_user")

    response = client.post(
        "/users/",
        headers=auth_headers(sales_manager_token),
        json={
            "username": username,
            "fullname": "Blocked User",
            "email": f"{username}@example.com",
            "password": "123456",
            "role_ids": [],
        },
    )

    assert response.status_code == 403