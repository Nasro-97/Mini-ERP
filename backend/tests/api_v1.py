from uuid import UUID
from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# =====================================================
# HELPERS
# =====================================================

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


def login(email: str, password: str) -> str:
    response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )

    assert response.status_code == 200, response.json()
    return response.json()["access_token"]


def login_as_cod() -> str:
    return login("cod@example.com", "123456")


def get_valid_sales_specialist_token() -> str:
    return login("sales.specialist@example.com", "123456")


def get_valid_sales_manager_token() -> str:
    return login("sales.manager@example.com", "123456")


def get_valid_client_id(token: str) -> str:
    # Helper to get an existing client id for request tests
    response = client.get("/clients/", headers=auth_headers(token))

    assert response.status_code == 200, response.json()

    clients = response.json()
    assert len(clients) > 0, "No clients found — create one first"

    return clients[0]["id"]


def create_request_payload(
    client_id: str,
    title_prefix: str,
    client_ref: str,
    priority: str = "low",
) -> dict:
    return {
        "request_data": {
            "request_number": unique_value("REQ"),
            "title": unique_value(title_prefix),
            "description": "Test request description",
            "client_reference": client_ref,
            "client_id": client_id,
            "priority": priority,
            "request_date": datetime.now().isoformat(),
            "deadline": "2026-12-31T00:00:00",
            "notes": "Test notes",
        }
    }


# =====================================================
# AUTH / USERS / ROLES
# =====================================================

def test_auth_and_users_me():
    token = login_as_cod()

    response = client.get(
        "/users/me",
        headers=auth_headers(token),
    )

    assert response.status_code == 200, response.json()

    data = response.json()
    assert data["email"] == "cod@example.com"
    assert data["is_active"] is True


def test_get_roles():
    token = login_as_cod()

    response = client.get(
        "/roles/",
        headers=auth_headers(token),
    )

    assert response.status_code == 200, response.json()

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

    assert create_response.status_code == 201, create_response.json()

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

    assert get_response.status_code == 200, get_response.json()
    assert get_response.json()["id"] == user_id

    # ---------- Update user ----------
    update_response = client.patch(
        f"/users/{user_id}",
        headers=auth_headers(token),
        json={
            "fullname": "Updated Test User",
        },
    )

    assert update_response.status_code == 200, update_response.json()
    assert update_response.json()["fullname"] == "Updated Test User"

    # ---------- Deactivate user ----------
    deactivate_response = client.patch(
        f"/users/{user_id}/deactivate",
        headers=auth_headers(token),
    )

    assert deactivate_response.status_code == 200, deactivate_response.json()
    assert deactivate_response.json()["is_active"] is False

    # ---------- Activate user ----------
    activate_response = client.patch(
        f"/users/{user_id}/activate",
        headers=auth_headers(token),
    )

    assert activate_response.status_code == 200, activate_response.json()
    assert activate_response.json()["is_active"] is True


# =====================================================
# CLIENTS / SUPPLIERS / CONTACTS
# =====================================================

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

    assert create_client_response.status_code == 201, create_client_response.json()

    client_data = create_client_response.json()
    client_id = client_data["id"]

    UUID(client_id)

    # ---------- Get all clients ----------
    get_clients_response = client.get(
        "/clients/",
        headers=auth_headers(token),
    )

    assert get_clients_response.status_code == 200, get_clients_response.json()
    assert isinstance(get_clients_response.json(), list)

    # ---------- Get client by ID ----------
    get_client_response = client.get(
        f"/clients/{client_id}",
        headers=auth_headers(token),
    )

    assert get_client_response.status_code == 200, get_client_response.json()
    assert get_client_response.json()["id"] == client_id

    # ---------- Update client ----------
    update_client_response = client.patch(
        f"/clients/{client_id}",
        headers=auth_headers(token),
        json={
            "address": "Updated Client Address",
        },
    )

    assert update_client_response.status_code == 200, update_client_response.json()
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

    assert activate_client_response.status_code == 200, activate_client_response.json()
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

    assert create_supplier_response.status_code == 201, create_supplier_response.json()

    supplier_data = create_supplier_response.json()
    supplier_id = supplier_data["id"]

    UUID(supplier_id)

    # ---------- Get all suppliers ----------
    get_suppliers_response = client.get(
        "/suppliers/",
        headers=auth_headers(token),
    )

    assert get_suppliers_response.status_code == 200, get_suppliers_response.json()
    assert isinstance(get_suppliers_response.json(), list)

    # ---------- Get supplier by ID ----------
    get_supplier_response = client.get(
        f"/suppliers/{supplier_id}",
        headers=auth_headers(token),
    )

    assert get_supplier_response.status_code == 200, get_supplier_response.json()
    assert get_supplier_response.json()["id"] == supplier_id

    # ---------- Update supplier ----------
    update_supplier_response = client.patch(
        f"/suppliers/{supplier_id}",
        headers=auth_headers(token),
        json={
            "address": "Updated Supplier Address",
        },
    )

    assert update_supplier_response.status_code == 200, update_supplier_response.json()
    assert update_supplier_response.json()["address"] == "Updated Supplier Address"

    # ---------- Deactivate supplier ----------
    deactivate_supplier_response = client.patch(
        f"/suppliers/{supplier_id}/deactivate",
        headers=auth_headers(token),
    )

    assert deactivate_supplier_response.status_code == 200, deactivate_supplier_response.json()
    assert deactivate_supplier_response.json()["is_active"] is False

    # ---------- Activate supplier ----------
    activate_supplier_response = client.patch(
        f"/suppliers/{supplier_id}/activate",
        headers=auth_headers(token),
    )

    assert activate_supplier_response.status_code == 200, activate_supplier_response.json()
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

    assert create_client_contact_response.status_code == 201, create_client_contact_response.json()

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

    assert get_contacts_response.status_code == 200, get_contacts_response.json()
    assert isinstance(get_contacts_response.json(), list)

    # ---------- Get contact by ID ----------
    get_contact_response = client.get(
        f"/contacts/{contact_id}",
        headers=auth_headers(token),
    )

    assert get_contact_response.status_code == 200, get_contact_response.json()
    assert get_contact_response.json()["id"] == contact_id

    # ---------- Get contacts by company ----------
    get_company_contacts_response = client.get(
        f"/contacts/company/client/{client_id}",
        headers=auth_headers(token),
    )

    assert get_company_contacts_response.status_code == 200, get_company_contacts_response.json()
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

    assert update_contact_response.status_code == 200, update_contact_response.json()
    assert update_contact_response.json()["position"] == "Updated Manager"

    # ---------- Deactivate contact ----------
    deactivate_contact_response = client.patch(
        f"/contacts/{contact_id}/deactivate",
        headers=auth_headers(token),
    )

    assert deactivate_contact_response.status_code == 200, deactivate_contact_response.json()
    assert deactivate_contact_response.json()["is_active"] is False

    # ---------- Activate contact ----------
    activate_contact_response = client.patch(
        f"/contacts/{contact_id}/activate",
        headers=auth_headers(token),
    )

    assert activate_contact_response.status_code == 200, activate_contact_response.json()
    assert activate_contact_response.json()["is_active"] is True


# =====================================================
# REQUESTS / ITEMS
# =====================================================

def test_request_full_flow():
    specialist_token = get_valid_sales_specialist_token()
    manager_token = get_valid_sales_manager_token()
    cod_token = login_as_cod()

    client_id = get_valid_client_id(cod_token)

    # ---------- Create request ----------
    create_response = client.post(
        "/requests/",
        headers=auth_headers(specialist_token),
        json=create_request_payload(
            client_id=client_id,
            title_prefix="test_request",
            client_ref="CLIENT-REF-001",
            priority="low",
        ),
    )

    assert create_response.status_code == 201, create_response.json()

    data = create_response.json()
    request_id = data["id"]

    assert data["status"] == "draft"

    # ---------- Add first item ----------
    item_1_response = client.post(
        f"/requests/{request_id}/items",
        headers=auth_headers(specialist_token),
        json={
            "description": "Hydraulic Pump HPU-450",
            "quantity": 4,
            "unit": "pcs",
            "notes": "Urgent",
        },
    )

    assert item_1_response.status_code == 201, item_1_response.json()

    # ---------- Add second item ----------
    item_2_response = client.post(
        f"/requests/{request_id}/items",
        headers=auth_headers(specialist_token),
        json={
            "description": "Hydraulic Hose Assembly",
            "quantity": 20,
            "unit": "pcs",
            "notes": None,
        },
    )

    assert item_2_response.status_code == 201, item_2_response.json()

    # ---------- Get request items ----------
    items_response = client.get(
        f"/requests/{request_id}/items",
        headers=auth_headers(specialist_token),
    )

    assert items_response.status_code == 200, items_response.json()
    assert len(items_response.json()) == 2

    # ---------- Get request by ID ----------
    get_response = client.get(
        f"/requests/{request_id}",
        headers=auth_headers(specialist_token),
    )

    assert get_response.status_code == 200, get_response.json()
    assert get_response.json()["id"] == request_id

    # ---------- Get all requests ----------
    list_response = client.get(
        "/requests/",
        headers=auth_headers(specialist_token),
    )

    assert list_response.status_code == 200, list_response.json()
    assert isinstance(list_response.json(), list)

    # ---------- Update request ----------
    update_response = client.patch(
        f"/requests/{request_id}",
        headers=auth_headers(specialist_token),
        json={
            "title": "Updated Request Title",
            "notes": "Some additional notes",
        },
    )

    assert update_response.status_code == 200, update_response.json()
    assert update_response.json()["title"] == "Updated Request Title"

    # ---------- Submit for review ----------
    submit_response = client.patch(
        f"/requests/{request_id}/submit",
        headers=auth_headers(specialist_token),
    )

    assert submit_response.status_code == 200, submit_response.json()
    assert submit_response.json()["status"] == "pending_sales_manager_approval"

    # ---------- Specialist cannot approve ----------
    blocked_approve = client.patch(
        f"/requests/{request_id}/approve",
        headers=auth_headers(specialist_token),
    )

    assert blocked_approve.status_code == 403, blocked_approve.json()

    # ---------- Manager approves ----------
    approve_response = client.patch(
        f"/requests/{request_id}/approve",
        headers=auth_headers(manager_token),
        params={"notes": "Looks good, proceed with sourcing"},
    )

    assert approve_response.status_code == 200, approve_response.json()
    assert approve_response.json()["status"] == "approved_for_sourcing"
    assert approve_response.json()["sales_manager_notes"] == "Looks good, proceed with sourcing"

    # ---------- Cannot submit again after approval ----------
    resubmit_response = client.patch(
        f"/requests/{request_id}/submit",
        headers=auth_headers(specialist_token),
    )

    assert resubmit_response.status_code == 400, resubmit_response.json()


def test_request_reject_flow():
    specialist_token = get_valid_sales_specialist_token()
    manager_token = get_valid_sales_manager_token()
    cod_token = login_as_cod()

    client_id = get_valid_client_id(cod_token)

    # ---------- Create request ----------
    create_response = client.post(
        "/requests/",
        headers=auth_headers(specialist_token),
        json=create_request_payload(
            client_id=client_id,
            title_prefix="reject_test_request",
            client_ref="CLIENT-REF-002",
            priority="normal",
        ),
    )

    assert create_response.status_code == 201, create_response.json()

    request_id = create_response.json()["id"]

    # ---------- Submit ----------
    submit_response = client.patch(
        f"/requests/{request_id}/submit",
        headers=auth_headers(specialist_token),
    )

    assert submit_response.status_code == 200, submit_response.json()

    # ---------- Manager rejects ----------
    reject_response = client.patch(
        f"/requests/{request_id}/reject",
        headers=auth_headers(manager_token),
        params={"notes": "Out of scope"},
    )

    assert reject_response.status_code == 200, reject_response.json()
    assert reject_response.json()["status"] == "rejected"
    assert reject_response.json()["sales_manager_notes"] == "Out of scope"


def test_delete_request_only_when_draft():
    specialist_token = get_valid_sales_specialist_token()
    cod_token = login_as_cod()

    client_id = get_valid_client_id(cod_token)

    # ---------- Create request ----------
    create_response = client.post(
        "/requests/",
        headers=auth_headers(specialist_token),
        json=create_request_payload(
            client_id=client_id,
            title_prefix="delete_test_request",
            client_ref="CLIENT-REF-003",
            priority="low",
        ),
    )

    assert create_response.status_code == 201, create_response.json()

    request_id = create_response.json()["id"]

    # ---------- Delete while draft ----------
    delete_response = client.delete(
        f"/requests/{request_id}",
        headers=auth_headers(specialist_token),
    )

    assert delete_response.status_code == 204

    # ---------- Confirm it is gone ----------
    get_response = client.get(
        f"/requests/{request_id}",
        headers=auth_headers(specialist_token),
    )

    assert get_response.status_code == 404, get_response.json()


def test_cannot_delete_submitted_request():
    specialist_token = get_valid_sales_specialist_token()
    cod_token = login_as_cod()

    client_id = get_valid_client_id(cod_token)

    create_response = client.post(
        "/requests/",
        headers=auth_headers(specialist_token),
        json=create_request_payload(
            client_id=client_id,
            title_prefix="no_delete_request",
            client_ref="CLIENT-REF-004",
            priority="low",
        ),
    )

    assert create_response.status_code == 201, create_response.json()

    request_id = create_response.json()["id"]

    submit_response = client.patch(
        f"/requests/{request_id}/submit",
        headers=auth_headers(specialist_token),
    )

    assert submit_response.status_code == 200, submit_response.json()

    delete_response = client.delete(
        f"/requests/{request_id}",
        headers=auth_headers(specialist_token),
    )

    assert delete_response.status_code == 400, delete_response.json()


def test_item_crud():
    specialist_token = get_valid_sales_specialist_token()
    cod_token = login_as_cod()

    client_id = get_valid_client_id(cod_token)

    # ---------- Create request ----------
    create_response = client.post(
        "/requests/",
        headers=auth_headers(specialist_token),
        json=create_request_payload(
            client_id=client_id,
            title_prefix="item_crud_request",
            client_ref="CLIENT-REF-005",
            priority="low",
        ),
    )

    assert create_response.status_code == 201, create_response.json()

    request_id = create_response.json()["id"]

    # ---------- Add item to request ----------
    add_item_response = client.post(
        f"/requests/{request_id}/items",
        headers=auth_headers(specialist_token),
        json={
            "description": "Pressure Gauge 0-400 bar",
            "quantity": 8,
            "unit": "pcs",
        },
    )

    assert add_item_response.status_code == 201, add_item_response.json()

    item_data = add_item_response.json()
    item_id = item_data["id"]

    assert item_data["line_number"] == 1
    assert item_data["description"] == "Pressure Gauge 0-400 bar"

    # ---------- Get items for request ----------
    items_response = client.get(
        f"/requests/{request_id}/items",
        headers=auth_headers(specialist_token),
    )

    assert items_response.status_code == 200, items_response.json()
    assert len(items_response.json()) == 1

    # ---------- Get item by ID ----------
    get_item_response = client.get(
        f"/items/{item_id}",
        headers=auth_headers(specialist_token),
    )

    assert get_item_response.status_code == 200, get_item_response.json()
    assert get_item_response.json()["id"] == item_id

    # ---------- Update item ----------
    update_item_response = client.patch(
        f"/items/{item_id}",
        headers=auth_headers(specialist_token),
        json={
            "description": "Updated Pressure Gauge",
            "quantity": 10,
        },
    )

    assert update_item_response.status_code == 200, update_item_response.json()
    assert update_item_response.json()["description"] == "Updated Pressure Gauge"

    # Quantity may return as int, float, or string depending on your schema/model
    assert str(update_item_response.json()["quantity"]) in ["10", "10.0"]

    # ---------- Delete item ----------
    delete_item_response = client.delete(
        f"/items/{item_id}",
        headers=auth_headers(specialist_token),
    )

    assert delete_item_response.status_code == 204

    # ---------- Confirm item is gone ----------
    get_deleted_response = client.get(
        f"/items/{item_id}",
        headers=auth_headers(specialist_token),
    )

    assert get_deleted_response.status_code == 404, get_deleted_response.json()


def test_sales_manager_sees_all_requests():
    manager_token = get_valid_sales_manager_token()

    response = client.get(
        "/requests/",
        headers=auth_headers(manager_token),
    )

    assert response.status_code == 200, response.json()
    assert isinstance(response.json(), list)


def test_specialist_only_sees_own_requests():
    specialist_token = get_valid_sales_specialist_token()

    response = client.get(
        "/requests/",
        headers=auth_headers(specialist_token),
    )

    assert response.status_code == 200, response.json()

    data = response.json()

    # Every request in the list must be assigned to this specialist
    me_response = client.get(
        "/users/me",
        headers=auth_headers(specialist_token),
    )

    assert me_response.status_code == 200, me_response.json()

    specialist_id = me_response.json()["id"]

    for req in data:
        assert req["assigned_to_user_id"] == specialist_id