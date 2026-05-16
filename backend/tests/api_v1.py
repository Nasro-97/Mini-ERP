from uuid import UUID
from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# =====================================================
# HELPERS
# =====================================================

def cleanup_test_users():
    token = login_as_cod()
    response = client.get("/users/", headers=auth_headers(token))
    assert response.status_code == 200
    users = response.json()
    for user in users:
        if user["username"].startswith("test_user_"):
            client.patch(
                f"/users/{user['id']}/deactivate",
                headers=auth_headers(token),
            )

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


def get_valid_procurement_manager_token() -> str:
    return login("procurement.manager@example.com", "123456")


def get_approved_for_sourcing_request_id(specialist_token: str, manager_token: str, client_id: str) -> str:
    # Creates a request and takes it all the way to approved_for_sourcing
    create_response = client.post(
        "/requests/",
        headers=auth_headers(specialist_token),
        json=create_request_payload(
            client_id=client_id,
            title_prefix="procurement_test_request",
            client_ref="PROC-REF-001",
            priority="high",
        ),
    )

    assert create_response.status_code == 201, create_response.json()
    request_id = create_response.json()["id"]

    submit_response = client.patch(
        f"/requests/{request_id}/submit",
        headers=auth_headers(specialist_token),
    )
    assert submit_response.status_code == 200, submit_response.json()

    approve_response = client.patch(
        f"/requests/{request_id}/approve",
        headers=auth_headers(manager_token),
        params={"notes": "Approved for sourcing"},
    )
    assert approve_response.status_code == 200, approve_response.json()
    assert approve_response.json()["status"] == "approved_for_sourcing"

    return request_id


def test_assign_procurement():
    specialist_token = get_valid_sales_specialist_token()
    manager_token = get_valid_sales_manager_token()
    procurement_manager_token = get_valid_procurement_manager_token()
    cod_token = login_as_cod()

    client_id = get_valid_client_id(cod_token)

    # ---------- Get procurement manager user id ----------
    me_response = client.get(
        "/users/me",
        headers=auth_headers(procurement_manager_token),
    )
    assert me_response.status_code == 200, me_response.json()
    procurement_manager_id = me_response.json()["id"]

    # ---------- Create a request and bring it to approved_for_sourcing ----------
    request_id = get_approved_for_sourcing_request_id(
        specialist_token, manager_token, client_id
    )

    # ---------- Sales specialist cannot assign procurement ----------
    blocked_response = client.patch(
        f"/requests/{request_id}/assign-procurement",
        headers=auth_headers(specialist_token),
        params={"assigned_user_id": procurement_manager_id},
    )
    assert blocked_response.status_code == 403, blocked_response.json()

    # ---------- Sales manager cannot assign procurement ----------
    blocked_response_2 = client.patch(
        f"/requests/{request_id}/assign-procurement",
        headers=auth_headers(manager_token),
        params={"assigned_user_id": procurement_manager_id},
    )
    assert blocked_response_2.status_code == 403, blocked_response_2.json()

    # ---------- Procurement manager assigns himself ----------
    assign_response = client.patch(
        f"/requests/{request_id}/assign-procurement",
        headers=auth_headers(procurement_manager_token),
        params={"assigned_user_id": procurement_manager_id},
    )
    assert assign_response.status_code == 200, assign_response.json()
    assert assign_response.json()["status"] == "rfq_in_progress"
    assert assign_response.json()["procurement_assigned_to_id"] == procurement_manager_id

    # ---------- Cannot assign again once already rfq_in_progress ----------
    reassign_response = client.patch(
        f"/requests/{request_id}/assign-procurement",
        headers=auth_headers(procurement_manager_token),
        params={"assigned_user_id": procurement_manager_id},
    )
    assert reassign_response.status_code == 400, reassign_response.json()

    # ---------- Cannot assign a sales user to procurement ----------
    specialist_id = client.get(
        "/users/me",
        headers=auth_headers(specialist_token),
    ).json()["id"]

    request_id_2 = get_approved_for_sourcing_request_id(
        specialist_token, manager_token, client_id
    )

    wrong_role_response = client.patch(
        f"/requests/{request_id_2}/assign-procurement",
        headers=auth_headers(procurement_manager_token),
        params={"assigned_user_id": specialist_id},
    )
    assert wrong_role_response.status_code == 400, wrong_role_response.json()

def get_valid_procurement_manager_token() -> str:
    return login("procurement.manager@example.com", "123456")


def get_valid_procurement_specialist_token() -> str:
    return login("procurement.specialist@example.com", "123456")


def get_valid_supplier_id(token: str) -> str:
    response = client.get("/suppliers/", headers=auth_headers(token))
    assert response.status_code == 200, response.json()
    suppliers = response.json()
    assert len(suppliers) > 0, "No suppliers found — create one first"
    return suppliers[0]["id"]


def create_rfq_in_progress_request(specialist_token: str, manager_token: str, procurement_manager_token: str, client_id: str) -> str:
    # Creates a request and brings it all the way to RFQ_IN_PROGRESS
    create_response = client.post(
        "/requests/",
        headers=auth_headers(specialist_token),
        json=create_request_payload(
            client_id=client_id,
            title_prefix="rfq_test_request",
            client_ref=unique_value("RFQ-REF"),
            priority="high",
        ),
    )
    assert create_response.status_code == 201, create_response.json()
    request_id = create_response.json()["id"]

    client.patch(
        f"/requests/{request_id}/submit",
        headers=auth_headers(specialist_token),
    )

    client.patch(
        f"/requests/{request_id}/approve",
        headers=auth_headers(manager_token),
        params={"notes": "Approved"},
    )

    pm_id = client.get(
        "/users/me",
        headers=auth_headers(procurement_manager_token),
    ).json()["id"]

    client.patch(
        f"/requests/{request_id}/assign-procurement",
        headers=auth_headers(procurement_manager_token),
        params={"assigned_user_id": pm_id},
    )

    return request_id


# =====================================================
# RFQ TESTS
# =====================================================

def test_rfq_full_flow():
    specialist_token = get_valid_sales_specialist_token()
    manager_token = get_valid_sales_manager_token()
    procurement_manager_token = get_valid_procurement_manager_token()
    cod_token = login_as_cod()

    client_id = get_valid_client_id(cod_token)
    supplier_id = get_valid_supplier_id(cod_token)

    request_id = create_rfq_in_progress_request(
        specialist_token, manager_token, procurement_manager_token, client_id
    )

    # ---------- Sales specialist cannot create RFQ ----------
    blocked_rfq = client.post(
        "/rfqs/",
        headers=auth_headers(specialist_token),
        json={
            "request_id": request_id,
            "supplier_id": supplier_id,
            "notes": "Test RFQ",
            "response_deadline": "2026-12-31T00:00:00",
        },
    )
    assert blocked_rfq.status_code == 403, blocked_rfq.json()

    # ---------- Procurement manager creates RFQ ----------
    create_rfq_response = client.post(
        "/rfqs/",
        headers=auth_headers(procurement_manager_token),
        json={
            "request_id": request_id,
            "supplier_id": supplier_id,
            "notes": "Please provide best quotation",
            "response_deadline": "2026-12-31T00:00:00",
        },
    )
    assert create_rfq_response.status_code == 201, create_rfq_response.json()

    rfq_data = create_rfq_response.json()
    rfq_id = rfq_data["id"]

    assert rfq_data["status"] == "draft"
    assert rfq_data["request_id"] == request_id
    assert rfq_data["supplier_id"] == supplier_id
    assert "RFQ-1" in rfq_data["rfq_number"]

    # ---------- Get RFQ by id ----------
    get_rfq_response = client.get(
        f"/rfqs/{rfq_id}",
        headers=auth_headers(procurement_manager_token),
    )
    assert get_rfq_response.status_code == 200, get_rfq_response.json()
    assert get_rfq_response.json()["id"] == rfq_id

    # ---------- Get RFQs by request ----------
    get_rfqs_response = client.get(
        f"/rfqs/request/{request_id}",
        headers=auth_headers(procurement_manager_token),
    )
    assert get_rfqs_response.status_code == 200, get_rfqs_response.json()
    assert len(get_rfqs_response.json()) == 1

    # ---------- Update RFQ ----------
    update_rfq_response = client.patch(
        f"/rfqs/{rfq_id}",
        headers=auth_headers(procurement_manager_token),
        json={"notes": "Updated notes"},
    )
    assert update_rfq_response.status_code == 200, update_rfq_response.json()
    assert update_rfq_response.json()["notes"] == "Updated notes"

    # ---------- Generate mailto ----------
    mailto_response = client.post(
        f"/rfqs/{rfq_id}/generate-mailto",
        headers=auth_headers(procurement_manager_token),
    )
    assert mailto_response.status_code == 200, mailto_response.json()

    mailto_data = mailto_response.json()
    assert "to" in mailto_data
    assert "subject" in mailto_data
    assert "body" in mailto_data
    assert "cc" in mailto_data

    # ---------- RFQ status is now SENT ----------
    get_sent_rfq = client.get(
        f"/rfqs/{rfq_id}",
        headers=auth_headers(procurement_manager_token),
    )
    assert get_sent_rfq.json()["status"] == "sent"

    # ---------- Cannot update after sent ----------
    blocked_update = client.patch(
        f"/rfqs/{rfq_id}",
        headers=auth_headers(procurement_manager_token),
        json={"notes": "Should not work"},
    )
    assert blocked_update.status_code == 400, blocked_update.json()

    # ---------- Cannot generate mailto again ----------
    blocked_mailto = client.post(
        f"/rfqs/{rfq_id}/generate-mailto",
        headers=auth_headers(procurement_manager_token),
    )
    assert blocked_mailto.status_code == 400, blocked_mailto.json()

    return rfq_id, request_id


def test_rfq_decline_closes_request():
    specialist_token = get_valid_sales_specialist_token()
    manager_token = get_valid_sales_manager_token()
    procurement_manager_token = get_valid_procurement_manager_token()
    cod_token = login_as_cod()

    client_id = get_valid_client_id(cod_token)
    supplier_id = get_valid_supplier_id(cod_token)

    request_id = create_rfq_in_progress_request(
        specialist_token, manager_token, procurement_manager_token, client_id
    )

    # ---------- Create and send RFQ ----------
    rfq_response = client.post(
        "/rfqs/",
        headers=auth_headers(procurement_manager_token),
        json={
            "request_id": request_id,
            "supplier_id": supplier_id,
            "response_deadline": "2026-12-31T00:00:00",
        },
    )
    assert rfq_response.status_code == 201, rfq_response.json()
    rfq_id = rfq_response.json()["id"]

    client.post(
        f"/rfqs/{rfq_id}/generate-mailto",
        headers=auth_headers(procurement_manager_token),
    )

    # ---------- Decline the RFQ ----------
    decline_response = client.patch(
        f"/rfqs/{rfq_id}/decline",
        headers=auth_headers(procurement_manager_token),
    )
    assert decline_response.status_code == 200, decline_response.json()
    assert decline_response.json()["status"] == "declined"

    # ---------- Request should now be CLOSED ----------
    request_response = client.get(
        f"/requests/{request_id}",
        headers=auth_headers(procurement_manager_token),
    )
    assert request_response.status_code == 200, request_response.json()
    assert request_response.json()["status"] == "closed"


def test_rfq_delete_only_when_draft():
    specialist_token = get_valid_sales_specialist_token()
    manager_token = get_valid_sales_manager_token()
    procurement_manager_token = get_valid_procurement_manager_token()
    cod_token = login_as_cod()

    client_id = get_valid_client_id(cod_token)
    supplier_id = get_valid_supplier_id(cod_token)

    request_id = create_rfq_in_progress_request(
        specialist_token, manager_token, procurement_manager_token, client_id
    )

    # ---------- Create RFQ ----------
    rfq_response = client.post(
        "/rfqs/",
        headers=auth_headers(procurement_manager_token),
        json={
            "request_id": request_id,
            "supplier_id": supplier_id,
            "response_deadline": "2026-12-31T00:00:00",
        },
    )
    rfq_id = rfq_response.json()["id"]

    # ---------- Delete while draft ----------
    delete_response = client.delete(
        f"/rfqs/{rfq_id}",
        headers=auth_headers(procurement_manager_token),
    )
    assert delete_response.status_code == 204

    # ---------- Confirm gone ----------
    get_response = client.get(
        f"/rfqs/{rfq_id}",
        headers=auth_headers(procurement_manager_token),
    )
    assert get_response.status_code == 404, get_response.json()


def test_procurement_specialist_can_create_rfq_on_assigned_request():
    specialist_token = get_valid_sales_specialist_token()
    manager_token = get_valid_sales_manager_token()
    procurement_manager_token = get_valid_procurement_manager_token()
    procurement_specialist_token = get_valid_procurement_specialist_token()
    cod_token = login_as_cod()

    client_id = get_valid_client_id(cod_token)
    supplier_id = get_valid_supplier_id(cod_token)

    # ---------- Create request and bring to approved_for_sourcing ----------
    create_response = client.post(
        "/requests/",
        headers=auth_headers(specialist_token),
        json=create_request_payload(
            client_id=client_id,
            title_prefix="specialist_rfq_request",
            client_ref=unique_value("SPEC-REF"),
        ),
    )
    request_id = create_response.json()["id"]

    client.patch(f"/requests/{request_id}/submit", headers=auth_headers(specialist_token))
    client.patch(
        f"/requests/{request_id}/approve",
        headers=auth_headers(manager_token),
        params={"notes": "Approved"},
    )

    # ---------- Assign to procurement specialist ----------
    specialist_id = client.get(
        "/users/me",
        headers=auth_headers(procurement_specialist_token),
    ).json()["id"]

    assign_response = client.patch(
        f"/requests/{request_id}/assign-procurement",
        headers=auth_headers(procurement_manager_token),
        params={"assigned_user_id": specialist_id},
    )
    assert assign_response.status_code == 200, assign_response.json()
    assert assign_response.json()["status"] == "rfq_in_progress"

    # ---------- Specialist creates RFQ on assigned request ----------
    rfq_response = client.post(
        "/rfqs/",
        headers=auth_headers(procurement_specialist_token),
        json={
            "request_id": request_id,
            "supplier_id": supplier_id,
            "response_deadline": "2026-12-31T00:00:00",
        },
    )
    assert rfq_response.status_code == 201, rfq_response.json()


# =====================================================
# QUOTATION TESTS
# =====================================================

def test_quotation_full_flow():
    specialist_token = get_valid_sales_specialist_token()
    manager_token = get_valid_sales_manager_token()
    procurement_manager_token = get_valid_procurement_manager_token()
    cod_token = login_as_cod()

    client_id = get_valid_client_id(cod_token)
    supplier_id = get_valid_supplier_id(cod_token)

    request_id = create_rfq_in_progress_request(
        specialist_token, manager_token, procurement_manager_token, client_id
    )

    # ---------- Create and send RFQ ----------
    rfq_response = client.post(
        "/rfqs/",
        headers=auth_headers(procurement_manager_token),
        json={
            "request_id": request_id,
            "supplier_id": supplier_id,
            "response_deadline": "2026-12-31T00:00:00",
        },
    )
    assert rfq_response.status_code == 201, rfq_response.json()
    rfq_id = rfq_response.json()["id"]

    client.post(
        f"/rfqs/{rfq_id}/generate-mailto",
        headers=auth_headers(procurement_manager_token),
    )

    # ---------- Create quotation ----------
    create_quotation_response = client.post(
        "/quotations/",
        headers=auth_headers(procurement_manager_token),
        json={
            "rfq_id": rfq_id,
            "currency": "USD",
            "subtotal": "45000.00",
            "shipping_cost": "1200.00",
            "taxes": "500.00",
            "other_costs": None,
            "total_amount": "46700.00",
            "payment_terms": "30% advance, 70% on delivery",
            "delivery_terms": "CIF Tripoli",
            "lead_time": "6-8 weeks",
            "validity_date": "2026-06-30T00:00:00",
            "notes": "Includes warranty 24 months",
        },
    )
    assert create_quotation_response.status_code == 201, create_quotation_response.json()

    quotation_data = create_quotation_response.json()
    quotation_id = quotation_data["id"]

    assert quotation_data["status"] == "received"
    assert quotation_data["rfq_id"] == rfq_id
    assert quotation_data["supplier_id"] == supplier_id

    # ---------- RFQ status should now be quote_received ----------
    rfq_check = client.get(
        f"/rfqs/{rfq_id}",
        headers=auth_headers(procurement_manager_token),
    )
    assert rfq_check.json()["status"] == "quote_received"

    # ---------- Request should now be in quotation_review ----------
    request_check = client.get(
        f"/requests/{request_id}",
        headers=auth_headers(procurement_manager_token),
    )
    assert request_check.json()["status"] == "quotation_review"

    # ---------- Get quotation by id ----------
    get_quotation_response = client.get(
        f"/quotations/{quotation_id}",
        headers=auth_headers(procurement_manager_token),
    )
    assert get_quotation_response.status_code == 200, get_quotation_response.json()
    assert get_quotation_response.json()["id"] == quotation_id

    # ---------- Get quotations by RFQ ----------
    get_by_rfq_response = client.get(
        f"/quotations/rfq/{rfq_id}",
        headers=auth_headers(procurement_manager_token),
    )
    assert get_by_rfq_response.status_code == 200, get_by_rfq_response.json()
    assert len(get_by_rfq_response.json()) == 1

    # ---------- Submit for review ----------
    submit_response = client.patch(
        f"/quotations/{quotation_id}/submit",
        headers=auth_headers(procurement_manager_token),
    )
    assert submit_response.status_code == 200, submit_response.json()
    assert submit_response.json()["status"] == "under_review"

    # ---------- Cannot submit again ----------
    blocked_submit = client.patch(
        f"/quotations/{quotation_id}/submit",
        headers=auth_headers(procurement_manager_token),
    )
    assert blocked_submit.status_code == 400, blocked_submit.json()

    # ---------- Approve quotation ----------
    approve_response = client.patch(
        f"/quotations/{quotation_id}/approve",
        headers=auth_headers(procurement_manager_token),
    )
    assert approve_response.status_code == 200, approve_response.json()
    assert approve_response.json()["status"] == "selected"

    # ---------- Request should now be offer_in_progress ----------
    request_final = client.get(
        f"/requests/{request_id}",
        headers=auth_headers(procurement_manager_token),
    )
    assert request_final.json()["status"] == "offer_in_progress"


def test_quotation_reject_and_reopen():
    specialist_token = get_valid_sales_specialist_token()
    manager_token = get_valid_sales_manager_token()
    procurement_manager_token = get_valid_procurement_manager_token()
    cod_token = login_as_cod()

    client_id = get_valid_client_id(cod_token)
    supplier_id = get_valid_supplier_id(cod_token)

    request_id = create_rfq_in_progress_request(
        specialist_token, manager_token, procurement_manager_token, client_id
    )

    # ---------- Create and send RFQ then register quotation ----------
    rfq_response = client.post(
        "/rfqs/",
        headers=auth_headers(procurement_manager_token),
        json={
            "request_id": request_id,
            "supplier_id": supplier_id,
            "response_deadline": "2026-12-31T00:00:00",
        },
    )
    rfq_id = rfq_response.json()["id"]

    client.post(
        f"/rfqs/{rfq_id}/generate-mailto",
        headers=auth_headers(procurement_manager_token),
    )

    quotation_response = client.post(
        "/quotations/",
        headers=auth_headers(procurement_manager_token),
        json={
            "rfq_id": rfq_id,
            "currency": "USD",
            "subtotal": "50000.00",
            "total_amount": "50000.00",
            "validity_date": "2026-06-30T00:00:00",
        },
    )
    quotation_id = quotation_response.json()["id"]

    # ---------- Submit for review ----------
    client.patch(
        f"/quotations/{quotation_id}/submit",
        headers=auth_headers(procurement_manager_token),
    )

    # ---------- Manager rejects ----------
    reject_response = client.patch(
        f"/quotations/{quotation_id}/reject",
        headers=auth_headers(procurement_manager_token),
        params={"rejection_notes": "Price is too high"},
    )
    assert reject_response.status_code == 200, reject_response.json()
    assert reject_response.json()["status"] == "rejected"
    assert reject_response.json()["rejection_notes"] == "Price is too high"

    # ---------- Reopen quotation ----------
    reopen_response = client.patch(
        f"/quotations/{quotation_id}/reopen",
        headers=auth_headers(procurement_manager_token),
    )
    assert reopen_response.status_code == 200, reopen_response.json()
    assert reopen_response.json()["status"] == "received"
    assert reopen_response.json()["rejection_notes"] is None


def test_auto_reject_other_quotations_on_submit():
    specialist_token = get_valid_sales_specialist_token()
    manager_token = get_valid_sales_manager_token()
    procurement_manager_token = get_valid_procurement_manager_token()
    cod_token = login_as_cod()

    client_id = get_valid_client_id(cod_token)

    # ---------- Need two different suppliers ----------
    suppliers_response = client.get("/suppliers/", headers=auth_headers(cod_token))
    suppliers = suppliers_response.json()
    assert len(suppliers) >= 2, "Need at least 2 suppliers for this test"
    supplier_id_1 = suppliers[0]["id"]
    supplier_id_2 = suppliers[1]["id"]

    request_id = create_rfq_in_progress_request(
        specialist_token, manager_token, procurement_manager_token, client_id
    )

    # ---------- Create two RFQs to two suppliers ----------
    rfq_1 = client.post(
        "/rfqs/",
        headers=auth_headers(procurement_manager_token),
        json={
            "request_id": request_id,
            "supplier_id": supplier_id_1,
            "response_deadline": "2026-12-31T00:00:00",
        },
    )
    rfq_id_1 = rfq_1.json()["id"]

    rfq_2 = client.post(
        "/rfqs/",
        headers=auth_headers(procurement_manager_token),
        json={
            "request_id": request_id,
            "supplier_id": supplier_id_2,
            "response_deadline": "2026-12-31T00:00:00",
        },
    )
    rfq_id_2 = rfq_2.json()["id"]

    # ---------- Send both RFQs ----------
    client.post(f"/rfqs/{rfq_id_1}/generate-mailto", headers=auth_headers(procurement_manager_token))
    client.post(f"/rfqs/{rfq_id_2}/generate-mailto", headers=auth_headers(procurement_manager_token))

    # ---------- Register quotation for each RFQ ----------
    q1_response = client.post(
        "/quotations/",
        headers=auth_headers(procurement_manager_token),
        json={
            "rfq_id": rfq_id_1,
            "currency": "USD",
            "subtotal": "45000.00",
            "total_amount": "45000.00",
            "validity_date": "2026-06-30T00:00:00",
        },
    )
    quotation_id_1 = q1_response.json()["id"]

    q2_response = client.post(
        "/quotations/",
        headers=auth_headers(procurement_manager_token),
        json={
            "rfq_id": rfq_id_2,
            "currency": "USD",
            "subtotal": "52000.00",
            "total_amount": "52000.00",
            "validity_date": "2026-06-30T00:00:00",
        },
    )
    quotation_id_2 = q2_response.json()["id"]

    # ---------- Submit quotation 1 for review ----------
    submit_response = client.patch(
        f"/quotations/{quotation_id_1}/submit",
        headers=auth_headers(procurement_manager_token),
    )
    assert submit_response.status_code == 200, submit_response.json()
    assert submit_response.json()["status"] == "under_review"

    # ---------- Quotation 2 should now be auto rejected ----------
    q2_check = client.get(
        f"/quotations/{quotation_id_2}",
        headers=auth_headers(procurement_manager_token),
    )
    assert q2_check.status_code == 200, q2_check.json()
    assert q2_check.json()["status"] == "rejected"


def test_cleanup_test_users():
    cleanup_test_users()