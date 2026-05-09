from uuid import UUID
from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def unique_value(prefix: str) -> str:
    # Creates unique strings so tests can run multiple times
    return f"{prefix}_{datetime.now().timestamp()}".replace(".", "_")


def unique_phone(prefix: str) -> str:
    # Creates unique phone numbers so unique database constraints do not fail
    suffix = str(int(datetime.now().timestamp() * 1000000))[-7:]
    return f"{prefix}{suffix}"


def auth_headers(token: str) -> dict:
    # Adds the JWT token to the request header
    return {"Authorization": f"Bearer {token}"}


def login_as_cod() -> str:
    # Logs in using your existing COD user
    response = client.post(
        "/auth/login",
        json={
            "email": "cod@example.com",
            "password": "123456",
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data

    return data["access_token"]


def test_auth_and_users_me():
    token = login_as_cod()

    response = client.get(
        "/users/me",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()
    assert data["email"] == "cod@example.com"
    assert data["is_active"] is True


def test_get_roles():
    token = login_as_cod()

    response = client.get(
        "/roles/",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert any(role["name"] == "COD" for role in data)
    assert any(role["name"] == "Sales Manager" for role in data)


def test_user_full_flow():
    token = login_as_cod()

    username = unique_value("test_user")
    email = f"{username}@example.com"

    # Existing Sales Manager role ID from your database
    sales_manager_role_id = "052eb3e8-1d10-49d4-a875-59dc9dfcbbc1"

    # ---------- Create user ----------
    create_response = client.post(
        "/users/",
        headers=auth_headers(token),
        json={
            "username": username,
            "fullname": "Test User",
            "email": email,
            "password": "123456",
            "role_ids": [sales_manager_role_id],
        },
    )

    assert create_response.status_code == 201

    user_data = create_response.json()
    user_id = user_data["id"]
    UUID(user_id)

    assert user_data["username"] == username
    assert user_data["email"] == email
    assert user_data["is_active"] is True

    # ---------- Get user by ID ----------
    get_response = client.get(
        f"/users/{user_id}",
        headers=auth_headers(token),
    )

    assert get_response.status_code == 200
    assert get_response.json()["id"] == user_id

    # ---------- Update user ----------
    update_response = client.patch(
        f"/users/{user_id}",
        headers=auth_headers(token),
        json={
            "fullname": "Updated Test User",
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["fullname"] == "Updated Test User"

    # ---------- Deactivate user ----------
    deactivate_response = client.patch(
        f"/users/{user_id}/deactivate",
        headers=auth_headers(token),
    )

    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["is_active"] is False

    # ---------- Activate user ----------
    activate_response = client.patch(
        f"/users/{user_id}/activate",
        headers=auth_headers(token),
    )

    assert activate_response.status_code == 200
    assert activate_response.json()["is_active"] is True


def test_client_supplier_contact_full_flow():
    token = login_as_cod()

    # =====================================================
    # CLIENT FLOW
    # =====================================================

    client_name = unique_value("client_company")

    # ---------- Create client ----------
    create_client_response = client.post(
        "/clients/",
        headers=auth_headers(token),
        json={
            "company_name": client_name,
            "email": f"{client_name}@example.com",
            "phone_1": unique_phone("091"),
            "phone_2": unique_phone("092"),
            "address": "Tripoli, Libya",
        },
    )

    assert create_client_response.status_code == 201

    client_data = create_client_response.json()
    client_id = client_data["id"]
    UUID(client_id)

    # ---------- Get all clients ----------
    get_clients_response = client.get(
        "/clients/",
        headers=auth_headers(token),
    )

    assert get_clients_response.status_code == 200
    assert isinstance(get_clients_response.json(), list)

    # ---------- Get client by ID ----------
    get_client_response = client.get(
        f"/clients/{client_id}",
        headers=auth_headers(token),
    )

    assert get_client_response.status_code == 200
    assert get_client_response.json()["id"] == client_id

    # ---------- Update client ----------
    update_client_response = client.patch(
        f"/clients/{client_id}",
        headers=auth_headers(token),
        json={
            "address": "Updated Client Address",
        },
    )

    assert update_client_response.status_code == 200
    assert update_client_response.json()["address"] == "Updated Client Address"

    # ---------- Deactivate client ----------
    deactivate_client_response = client.patch(
        f"/clients/{client_id}/deactivate",
        headers=auth_headers(token),
    )

    assert deactivate_client_response.status_code == 200, deactivate_client_response.json()
    assert deactivate_client_response.json()["is_active"] is False

    # ---------- Activate client ----------
    activate_client_response = client.patch(
        f"/clients/{client_id}/activate",
        headers=auth_headers(token),
    )

    assert activate_client_response.status_code == 200
    assert activate_client_response.json()["is_active"] is True

    # =====================================================
    # SUPPLIER FLOW
    # =====================================================

    supplier_name = unique_value("supplier_company")

    # ---------- Create supplier ----------
    create_supplier_response = client.post(
        "/suppliers/",
        headers=auth_headers(token),
        json={
            "company_name": supplier_name,
            "email": f"{supplier_name}@example.com",
            "phone_1": unique_phone("093"),
            "phone_2": unique_phone("094"),
            "address": "Misrata, Libya",
        },
    )

    assert create_supplier_response.status_code == 201

    supplier_data = create_supplier_response.json()
    supplier_id = supplier_data["id"]
    UUID(supplier_id)

    # ---------- Get all suppliers ----------
    get_suppliers_response = client.get(
        "/suppliers/",
        headers=auth_headers(token),
    )

    assert get_suppliers_response.status_code == 200
    assert isinstance(get_suppliers_response.json(), list)

    # ---------- Get supplier by ID ----------
    get_supplier_response = client.get(
        f"/suppliers/{supplier_id}",
        headers=auth_headers(token),
    )

    assert get_supplier_response.status_code == 200
    assert get_supplier_response.json()["id"] == supplier_id

    # ---------- Update supplier ----------
    update_supplier_response = client.patch(
        f"/suppliers/{supplier_id}",
        headers=auth_headers(token),
        json={
            "address": "Updated Supplier Address",
        },
    )

    assert update_supplier_response.status_code == 200
    assert update_supplier_response.json()["address"] == "Updated Supplier Address"

    # ---------- Deactivate supplier ----------
    deactivate_supplier_response = client.patch(
        f"/suppliers/{supplier_id}/deactivate",
        headers=auth_headers(token),
    )


    assert deactivate_supplier_response.status_code == 200
    assert deactivate_supplier_response.json()["is_active"] is False

    # ---------- Activate supplier ----------
    activate_supplier_response = client.patch(
        f"/suppliers/{supplier_id}/activate",
        headers=auth_headers(token),
    )

    assert activate_supplier_response.status_code == 200
    assert activate_supplier_response.json()["is_active"] is True

    # =====================================================
    # CONTACT FLOW
    # =====================================================

    client_contact_email = f"{unique_value('client_contact')}@example.com"

    # ---------- Create client contact ----------
    create_client_contact_response = client.post(
        "/contacts/",
        headers=auth_headers(token),
        json={
            "company_type": "client",
            "company_id": client_id,
            "fullname": "Client Contact Person",
            "position": "Manager",
            "email": client_contact_email,
            "phone_1": unique_phone("095"),
            "phone_2": unique_phone("096"),
        },
    )

    assert create_client_contact_response.status_code == 201

    contact_data = create_client_contact_response.json()
    contact_id = contact_data["id"]
    UUID(contact_id)

    assert contact_data["company_type"] == "client"
    assert contact_data["company_id"] == client_id

    # ---------- Get all contacts ----------
    get_contacts_response = client.get(
        "/contacts/",
        headers=auth_headers(token),
    )

    assert get_contacts_response.status_code == 200
    assert isinstance(get_contacts_response.json(), list)

    # ---------- Get contact by ID ----------
    get_contact_response = client.get(
        f"/contacts/{contact_id}",
        headers=auth_headers(token),
    )

    assert get_contact_response.status_code == 200
    assert get_contact_response.json()["id"] == contact_id

    # ---------- Get contacts by company ----------
    get_company_contacts_response = client.get(
        f"/contacts/company/client/{client_id}",
        headers=auth_headers(token),
    )

    assert get_company_contacts_response.status_code == 200
    assert isinstance(get_company_contacts_response.json(), list)
    assert any(contact["id"] == contact_id for contact in get_company_contacts_response.json())

    # ---------- Update contact ----------
    update_contact_response = client.patch(
        f"/contacts/{contact_id}",
        headers=auth_headers(token),
        json={
            "position": "Updated Manager",
        },
    )

    assert update_contact_response.status_code == 200
    assert update_contact_response.json()["position"] == "Updated Manager"

    # ---------- Deactivate contact ----------
    deactivate_contact_response = client.patch(
        f"/contacts/{contact_id}/deactivate",
        headers=auth_headers(token),
    )

    assert deactivate_contact_response.status_code == 200
    assert deactivate_contact_response.json()["is_active"] is False

    # ---------- Activate contact ----------
    activate_contact_response = client.patch(
        f"/contacts/{contact_id}/activate",
        headers=auth_headers(token),
    )

    assert activate_contact_response.status_code == 200
    assert activate_contact_response.json()["is_active"] is True