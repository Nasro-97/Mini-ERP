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
            client.patch(f"/users/{user['id']}/deactivate", headers=auth_headers(token))


def unique_value(prefix: str) -> str:
    return f"{prefix}_{datetime.now().timestamp()}".replace(".", "_")


def unique_phone(prefix: str) -> str:
    suffix = str(int(datetime.now().timestamp() * 1000000))[-7:]
    return f"{prefix}{suffix}"


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def login(email: str, password: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.json()
    return response.json()["access_token"]


def login_as_cod() -> str:
    return login("cod@example.com", "123456")


def get_valid_sales_specialist_token() -> str:
    return login("sales.specialist@example.com", "123456")


def get_valid_sales_manager_token() -> str:
    return login("sales.manager@example.com", "123456")


def get_valid_procurement_manager_token() -> str:
    return login("procurement.manager@example.com", "123456")


def get_valid_procurement_specialist_token() -> str:
    return login("procurement.specialist@example.com", "123456")


def get_valid_client_id(token: str) -> str:
    response = client.get("/clients/", headers=auth_headers(token))
    assert response.status_code == 200, response.json()
    clients = response.json()
    assert len(clients) > 0, "No clients found — create one first"
    return clients[0]["id"]


def get_valid_supplier_id(token: str) -> str:
    response = client.get("/suppliers/", headers=auth_headers(token))
    assert response.status_code == 200, response.json()
    suppliers = response.json()
    assert len(suppliers) > 0, "No suppliers found — create one first"
    return suppliers[0]["id"]


def create_request_payload(client_id: str, title_prefix: str, client_ref: str, priority: str = "low") -> dict:
    return {
        "request_data": {
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


def add_request_items(request_id: str, token: str) -> list[str]:
    """Adds two standard items to a request and returns their IDs."""
    item_1 = client.post(
        f"/requests/{request_id}/items",
        headers=auth_headers(token),
        json={"description": "Hydraulic Pump HPU-450", "quantity": 4, "unit": "pcs"},
    )
    assert item_1.status_code == 201, item_1.json()

    item_2 = client.post(
        f"/requests/{request_id}/items",
        headers=auth_headers(token),
        json={"description": "Hydraulic Hose Assembly", "quantity": 20, "unit": "pcs"},
    )
    assert item_2.status_code == 201, item_2.json()

    return [item_1.json()["id"], item_2.json()["id"]]


def get_approved_for_sourcing_request_id(specialist_token: str, manager_token: str, client_id: str) -> str:
    create_response = client.post(
        "/requests/",
        headers=auth_headers(specialist_token),
        json=create_request_payload(
            client_id=client_id,
            title_prefix="procurement_test_request",
            client_ref=unique_value("PROC-REF"),
            priority="high",
        ),
    )
    assert create_response.status_code == 201, create_response.json()
    request_id = create_response.json()["id"]

    # Always add items — they flow through the entire pipeline
    add_request_items(request_id, specialist_token)

    client.patch(f"/requests/{request_id}/submit", headers=auth_headers(specialist_token))
    client.patch(
        f"/requests/{request_id}/approve",
        headers=auth_headers(manager_token),
        params={"notes": "Approved for sourcing"},
    )
    return request_id


def create_rfq_in_progress_request(
    specialist_token: str,
    manager_token: str,
    procurement_manager_token: str,
    client_id: str,
) -> str:
    request_id = get_approved_for_sourcing_request_id(specialist_token, manager_token, client_id)

    pm_id = client.get("/users/me", headers=auth_headers(procurement_manager_token)).json()["id"]
    client.patch(
        f"/requests/{request_id}/assign-procurement",
        headers=auth_headers(procurement_manager_token),
        params={"assigned_user_id": pm_id},
    )
    return request_id


def create_offer_in_progress_request(
    specialist_token: str,
    manager_token: str,
    procurement_manager_token: str,
    client_id: str,
    supplier_id: str,
) -> tuple[str, str]:
    # Returns (request_id, quotation_id)
    request_id = create_rfq_in_progress_request(
        specialist_token, manager_token, procurement_manager_token, client_id
    )

    rfq_response = client.post(
        "/rfqs/",
        headers=auth_headers(procurement_manager_token),
        json={"request_id": request_id, "supplier_id": supplier_id, "response_deadline": "2026-12-31T00:00:00"},
    )
    assert rfq_response.status_code == 201, rfq_response.json()
    rfq_id = rfq_response.json()["id"]

    client.post(f"/rfqs/{rfq_id}/generate-mailto", headers=auth_headers(procurement_manager_token))

    quotation_response = client.post(
        "/quotations/",
        headers=auth_headers(procurement_manager_token),
        json={
            "rfq_id": rfq_id,
            "currency": "USD",
            "subtotal": "45000.00",
            "total_amount": "46700.00",
            "validity_date": "2026-06-30T00:00:00",
            "payment_terms": "30% advance, 70% on delivery",
            "delivery_terms": "CIF Tripoli",
            "lead_time": "6-8 weeks",
            "notes": "Includes warranty 24 months",
        },
    )
    assert quotation_response.status_code == 201, quotation_response.json()
    quotation_id = quotation_response.json()["id"]

    client.patch(f"/quotations/{quotation_id}/submit", headers=auth_headers(procurement_manager_token))
    client.patch(f"/quotations/{quotation_id}/approve", headers=auth_headers(procurement_manager_token))

    return request_id, quotation_id


def create_approved_by_client_request(
    specialist_token: str,
    manager_token: str,
    procurement_manager_token: str,
    cod_token: str,
    client_id: str,
    supplier_id: str,
) -> tuple[str, str, str]:
    # Returns (request_id, quotation_id, offer_version_id)
    request_id, quotation_id = create_offer_in_progress_request(
        specialist_token, manager_token, procurement_manager_token, client_id, supplier_id
    )

    create_offer_response = client.post(
        "/offers/",
        headers=auth_headers(specialist_token),
        json={"request_id": request_id, "quotation_id": quotation_id},
    )
    assert create_offer_response.status_code == 201, create_offer_response.json()
    offer_id = create_offer_response.json()["id"]

    offer_response = client.get(f"/offers/{offer_id}", headers=auth_headers(specialist_token))
    version_id = offer_response.json()["versions"][0]["id"]

    client.patch(f"/offers/versions/{version_id}/submit", headers=auth_headers(specialist_token))
    client.patch(
        f"/offers/versions/{version_id}/cod-response",
        headers=auth_headers(cod_token),
        json={"cod_status": "approved", "cod_notes": None},
    )
    client.patch(f"/offers/versions/{version_id}/send", headers=auth_headers(specialist_token))
    client.patch(
        f"/offers/versions/{version_id}/client-response",
        headers=auth_headers(specialist_token),
        json={"client_status": "approved", "client_notes": "Approved"},
    )

    return request_id, quotation_id, version_id


# =====================================================
# AUTH / USERS / ROLES
# =====================================================

def test_auth_and_users_me():
    token = login_as_cod()
    response = client.get("/users/me", headers=auth_headers(token))
    assert response.status_code == 200, response.json()
    data = response.json()
    assert data["email"] == "cod@example.com"
    assert data["is_active"] is True


def test_get_roles():
    token = login_as_cod()
    response = client.get("/roles/", headers=auth_headers(token))
    assert response.status_code == 200, response.json()
    data = response.json()
    assert isinstance(data, list)
    assert any(role["name"] == "COD" for role in data)
    assert any(role["name"] == "Sales Manager" for role in data)


def test_user_full_flow():
    token = login_as_cod()
    username = unique_value("test_user")
    email = f"{username}@example.com"
    sales_manager_role_id = "052eb3e8-1d10-49d4-a875-59dc9dfcbbc1"

    create_response = client.post(
        "/users/",
        headers=auth_headers(token),
        json={"username": username, "fullname": "Test User", "email": email, "password": "123456", "role_ids": [sales_manager_role_id]},
    )
    assert create_response.status_code == 201, create_response.json()
    user_data = create_response.json()
    user_id = user_data["id"]
    UUID(user_id)
    assert user_data["username"] == username
    assert user_data["is_active"] is True

    get_response = client.get(f"/users/{user_id}", headers=auth_headers(token))
    assert get_response.status_code == 200, get_response.json()

    update_response = client.patch(f"/users/{user_id}", headers=auth_headers(token), json={"fullname": "Updated Test User"})
    assert update_response.status_code == 200, update_response.json()
    assert update_response.json()["fullname"] == "Updated Test User"

    deactivate_response = client.patch(f"/users/{user_id}/deactivate", headers=auth_headers(token))
    assert deactivate_response.status_code == 200, deactivate_response.json()
    assert deactivate_response.json()["is_active"] is False

    activate_response = client.patch(f"/users/{user_id}/activate", headers=auth_headers(token))
    assert activate_response.status_code == 200, activate_response.json()
    assert activate_response.json()["is_active"] is True


# =====================================================
# CLIENTS / SUPPLIERS / CONTACTS
# =====================================================

def test_client_supplier_contact_full_flow():
    token = login_as_cod()

    client_name = unique_value("client_company")
    create_client_response = client.post(
        "/clients/",
        headers=auth_headers(token),
        json={"company_name": client_name, "email": f"{client_name}@example.com", "phone_1": unique_phone("091"), "phone_2": unique_phone("092"), "address": "Tripoli, Libya"},
    )
    assert create_client_response.status_code == 201, create_client_response.json()
    client_id = create_client_response.json()["id"]

    assert client.get(f"/clients/{client_id}", headers=auth_headers(token)).status_code == 200
    assert client.patch(f"/clients/{client_id}", headers=auth_headers(token), json={"address": "Updated"}).json()["address"] == "Updated"
    assert client.patch(f"/clients/{client_id}/deactivate", headers=auth_headers(token)).json()["is_active"] is False
    assert client.patch(f"/clients/{client_id}/activate", headers=auth_headers(token)).json()["is_active"] is True

    supplier_name = unique_value("supplier_company")
    create_supplier_response = client.post(
        "/suppliers/",
        headers=auth_headers(token),
        json={"company_name": supplier_name, "email": f"{supplier_name}@example.com", "phone_1": unique_phone("093"), "phone_2": unique_phone("094"), "address": "Misrata, Libya"},
    )
    assert create_supplier_response.status_code == 201, create_supplier_response.json()
    supplier_id = create_supplier_response.json()["id"]

    assert client.get(f"/suppliers/{supplier_id}", headers=auth_headers(token)).status_code == 200
    assert client.patch(f"/suppliers/{supplier_id}", headers=auth_headers(token), json={"address": "Updated"}).json()["address"] == "Updated"
    assert client.patch(f"/suppliers/{supplier_id}/deactivate", headers=auth_headers(token)).json()["is_active"] is False
    assert client.patch(f"/suppliers/{supplier_id}/activate", headers=auth_headers(token)).json()["is_active"] is True

    contact_email = f"{unique_value('contact')}@example.com"
    create_contact_response = client.post(
        "/contacts/",
        headers=auth_headers(token),
        json={"company_type": "client", "company_id": client_id, "fullname": "Contact Person", "position": "Manager", "email": contact_email, "phone_1": unique_phone("095"), "phone_2": unique_phone("096")},
    )
    assert create_contact_response.status_code == 201, create_contact_response.json()
    contact_id = create_contact_response.json()["id"]

    assert client.get(f"/contacts/{contact_id}", headers=auth_headers(token)).status_code == 200
    assert client.patch(f"/contacts/{contact_id}", headers=auth_headers(token), json={"position": "Updated"}).json()["position"] == "Updated"
    assert client.patch(f"/contacts/{contact_id}/deactivate", headers=auth_headers(token)).json()["is_active"] is False
    assert client.patch(f"/contacts/{contact_id}/activate", headers=auth_headers(token)).json()["is_active"] is True


# =====================================================
# REQUESTS / ITEMS
# =====================================================

def test_request_full_flow():
    specialist_token = get_valid_sales_specialist_token()
    manager_token = get_valid_sales_manager_token()
    cod_token = login_as_cod()
    client_id = get_valid_client_id(cod_token)

    create_response = client.post(
        "/requests/",
        headers=auth_headers(specialist_token),
        json=create_request_payload(client_id=client_id, title_prefix="test_request", client_ref="CLIENT-REF-001"),
    )
    assert create_response.status_code == 201, create_response.json()
    request_id = create_response.json()["id"]
    assert create_response.json()["status"] == "draft"

    # ---------- Add items ----------
    item_ids = add_request_items(request_id, specialist_token)
    assert len(item_ids) == 2

    # ---------- Verify items ----------
    items_response = client.get(f"/requests/{request_id}/items", headers=auth_headers(specialist_token))
    assert items_response.status_code == 200, items_response.json()
    assert len(items_response.json()) == 2
    assert items_response.json()[0]["line_number"] == 1
    assert items_response.json()[1]["line_number"] == 2

    # ---------- Update an item ----------
    update_item = client.patch(
        f"/items/{item_ids[0]}",
        headers=auth_headers(specialist_token),
        json={"description": "Updated Hydraulic Pump", "quantity": 6},
    )
    assert update_item.status_code == 200, update_item.json()
    assert update_item.json()["description"] == "Updated Hydraulic Pump"

    # ---------- Delete second item and verify ----------
    delete_item = client.delete(f"/items/{item_ids[1]}", headers=auth_headers(specialist_token))
    assert delete_item.status_code == 204

    items_after_delete = client.get(f"/requests/{request_id}/items", headers=auth_headers(specialist_token))
    assert len(items_after_delete.json()) == 1

    # ---------- Add it back ----------
    add_back = client.post(
        f"/requests/{request_id}/items",
        headers=auth_headers(specialist_token),
        json={"description": "Hydraulic Hose Assembly", "quantity": 20, "unit": "pcs"},
    )
    assert add_back.status_code == 201, add_back.json()

    # ---------- Update request fields ----------
    update_response = client.patch(
        f"/requests/{request_id}",
        headers=auth_headers(specialist_token),
        json={"title": "Updated Request Title"},
    )
    assert update_response.status_code == 200, update_response.json()
    assert update_response.json()["title"] == "Updated Request Title"

    # ---------- Submit ----------
    submit_response = client.patch(f"/requests/{request_id}/submit", headers=auth_headers(specialist_token))
    assert submit_response.status_code == 200, submit_response.json()
    assert submit_response.json()["status"] == "pending_sales_manager_approval"

    # ---------- Cannot add items after submit ----------
    blocked_item = client.post(
        f"/requests/{request_id}/items",
        headers=auth_headers(specialist_token),
        json={"description": "Should not work", "quantity": 1, "unit": "pcs"},
    )
    assert blocked_item.status_code == 400, blocked_item.json()

    # ---------- Specialist cannot approve ----------
    assert client.patch(f"/requests/{request_id}/approve", headers=auth_headers(specialist_token)).status_code == 403

    # ---------- Manager approves ----------
    approve_response = client.patch(
        f"/requests/{request_id}/approve",
        headers=auth_headers(manager_token),
        params={"notes": "Looks good"},
    )
    assert approve_response.status_code == 200, approve_response.json()
    assert approve_response.json()["status"] == "approved_for_sourcing"

    # ---------- Cannot submit again ----------
    assert client.patch(f"/requests/{request_id}/submit", headers=auth_headers(specialist_token)).status_code == 400


def test_request_reject_flow():
    specialist_token = get_valid_sales_specialist_token()
    manager_token = get_valid_sales_manager_token()
    cod_token = login_as_cod()
    client_id = get_valid_client_id(cod_token)

    create_response = client.post(
        "/requests/",
        headers=auth_headers(specialist_token),
        json=create_request_payload(client_id=client_id, title_prefix="reject_request", client_ref="CLIENT-REF-002", priority="normal"),
    )
    assert create_response.status_code == 201, create_response.json()
    request_id = create_response.json()["id"]

    add_request_items(request_id, specialist_token)
    client.patch(f"/requests/{request_id}/submit", headers=auth_headers(specialist_token))

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

    create_response = client.post(
        "/requests/",
        headers=auth_headers(specialist_token),
        json=create_request_payload(client_id=client_id, title_prefix="delete_request", client_ref="CLIENT-REF-003"),
    )
    request_id = create_response.json()["id"]
    add_request_items(request_id, specialist_token)

    delete_response = client.delete(f"/requests/{request_id}", headers=auth_headers(specialist_token))
    assert delete_response.status_code == 204

    assert client.get(f"/requests/{request_id}", headers=auth_headers(specialist_token)).status_code == 404


def test_cannot_delete_submitted_request():
    specialist_token = get_valid_sales_specialist_token()
    cod_token = login_as_cod()
    client_id = get_valid_client_id(cod_token)

    create_response = client.post(
        "/requests/",
        headers=auth_headers(specialist_token),
        json=create_request_payload(client_id=client_id, title_prefix="no_delete_request", client_ref="CLIENT-REF-004"),
    )
    request_id = create_response.json()["id"]
    add_request_items(request_id, specialist_token)
    client.patch(f"/requests/{request_id}/submit", headers=auth_headers(specialist_token))

    assert client.delete(f"/requests/{request_id}", headers=auth_headers(specialist_token)).status_code == 400


def test_sales_manager_sees_all_requests():
    manager_token = get_valid_sales_manager_token()
    response = client.get("/requests/", headers=auth_headers(manager_token))
    assert response.status_code == 200, response.json()
    assert isinstance(response.json(), list)


def test_specialist_only_sees_own_requests():
    specialist_token = get_valid_sales_specialist_token()
    response = client.get("/requests/", headers=auth_headers(specialist_token))
    assert response.status_code == 200, response.json()
    specialist_id = client.get("/users/me", headers=auth_headers(specialist_token)).json()["id"]
    for req in response.json():
        assert req["assigned_to_user_id"] == specialist_id


# =====================================================
# PROCUREMENT ASSIGNMENT
# =====================================================

def test_assign_procurement():
    specialist_token = get_valid_sales_specialist_token()
    manager_token = get_valid_sales_manager_token()
    procurement_manager_token = get_valid_procurement_manager_token()
    cod_token = login_as_cod()
    client_id = get_valid_client_id(cod_token)

    procurement_manager_id = client.get("/users/me", headers=auth_headers(procurement_manager_token)).json()["id"]
    request_id = get_approved_for_sourcing_request_id(specialist_token, manager_token, client_id)

    assert client.patch(f"/requests/{request_id}/assign-procurement", headers=auth_headers(specialist_token), params={"assigned_user_id": procurement_manager_id}).status_code == 403
    assert client.patch(f"/requests/{request_id}/assign-procurement", headers=auth_headers(manager_token), params={"assigned_user_id": procurement_manager_id}).status_code == 403

    assign_response = client.patch(
        f"/requests/{request_id}/assign-procurement",
        headers=auth_headers(procurement_manager_token),
        params={"assigned_user_id": procurement_manager_id},
    )
    assert assign_response.status_code == 200, assign_response.json()
    assert assign_response.json()["status"] == "rfq_in_progress"
    assert assign_response.json()["procurement_assigned_to_id"] == procurement_manager_id

    assert client.patch(f"/requests/{request_id}/assign-procurement", headers=auth_headers(procurement_manager_token), params={"assigned_user_id": procurement_manager_id}).status_code == 400

    specialist_id = client.get("/users/me", headers=auth_headers(specialist_token)).json()["id"]
    request_id_2 = get_approved_for_sourcing_request_id(specialist_token, manager_token, client_id)
    assert client.patch(f"/requests/{request_id_2}/assign-procurement", headers=auth_headers(procurement_manager_token), params={"assigned_user_id": specialist_id}).status_code == 400


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

    request_id = create_rfq_in_progress_request(specialist_token, manager_token, procurement_manager_token, client_id)

    # ---------- Verify items exist on request ----------
    items = client.get(f"/requests/{request_id}/items", headers=auth_headers(procurement_manager_token))
    assert items.status_code == 200
    assert len(items.json()) == 2

    assert client.post("/rfqs/", headers=auth_headers(specialist_token), json={"request_id": request_id, "supplier_id": supplier_id, "response_deadline": "2026-12-31T00:00:00"}).status_code == 403

    create_rfq_response = client.post(
        "/rfqs/",
        headers=auth_headers(procurement_manager_token),
        json={"request_id": request_id, "supplier_id": supplier_id, "notes": "Please provide best quotation", "response_deadline": "2026-12-31T00:00:00"},
    )
    assert create_rfq_response.status_code == 201, create_rfq_response.json()
    rfq_id = create_rfq_response.json()["id"]
    assert create_rfq_response.json()["status"] == "draft"
    assert "RFQ-1" in create_rfq_response.json()["rfq_number"]

    assert client.get(f"/rfqs/{rfq_id}", headers=auth_headers(procurement_manager_token)).status_code == 200
    assert len(client.get(f"/rfqs/request/{request_id}", headers=auth_headers(procurement_manager_token)).json()) == 1

    update_rfq = client.patch(f"/rfqs/{rfq_id}", headers=auth_headers(procurement_manager_token), json={"notes": "Updated notes"})
    assert update_rfq.status_code == 200
    assert update_rfq.json()["notes"] == "Updated notes"

    mailto_response = client.post(f"/rfqs/{rfq_id}/generate-mailto", headers=auth_headers(procurement_manager_token))
    assert mailto_response.status_code == 200
    assert all(k in mailto_response.json() for k in ["to", "subject", "body", "cc"])

    assert client.get(f"/rfqs/{rfq_id}", headers=auth_headers(procurement_manager_token)).json()["status"] == "sent"
    assert client.patch(f"/rfqs/{rfq_id}", headers=auth_headers(procurement_manager_token), json={"notes": "Should not work"}).status_code == 400
    assert client.post(f"/rfqs/{rfq_id}/generate-mailto", headers=auth_headers(procurement_manager_token)).status_code == 400


def test_rfq_decline_closes_request():
    specialist_token = get_valid_sales_specialist_token()
    manager_token = get_valid_sales_manager_token()
    procurement_manager_token = get_valid_procurement_manager_token()
    cod_token = login_as_cod()
    client_id = get_valid_client_id(cod_token)
    supplier_id = get_valid_supplier_id(cod_token)

    request_id = create_rfq_in_progress_request(specialist_token, manager_token, procurement_manager_token, client_id)
    rfq_response = client.post("/rfqs/", headers=auth_headers(procurement_manager_token), json={"request_id": request_id, "supplier_id": supplier_id, "response_deadline": "2026-12-31T00:00:00"})
    rfq_id = rfq_response.json()["id"]
    client.post(f"/rfqs/{rfq_id}/generate-mailto", headers=auth_headers(procurement_manager_token))

    decline_response = client.patch(f"/rfqs/{rfq_id}/decline", headers=auth_headers(procurement_manager_token))
    assert decline_response.status_code == 200
    assert decline_response.json()["status"] == "declined"
    assert client.get(f"/requests/{request_id}", headers=auth_headers(procurement_manager_token)).json()["status"] == "closed"


def test_rfq_delete_only_when_draft():
    specialist_token = get_valid_sales_specialist_token()
    manager_token = get_valid_sales_manager_token()
    procurement_manager_token = get_valid_procurement_manager_token()
    cod_token = login_as_cod()
    client_id = get_valid_client_id(cod_token)
    supplier_id = get_valid_supplier_id(cod_token)

    request_id = create_rfq_in_progress_request(specialist_token, manager_token, procurement_manager_token, client_id)
    rfq_id = client.post("/rfqs/", headers=auth_headers(procurement_manager_token), json={"request_id": request_id, "supplier_id": supplier_id, "response_deadline": "2026-12-31T00:00:00"}).json()["id"]

    assert client.delete(f"/rfqs/{rfq_id}", headers=auth_headers(procurement_manager_token)).status_code == 204
    assert client.get(f"/rfqs/{rfq_id}", headers=auth_headers(procurement_manager_token)).status_code == 404


def test_procurement_specialist_can_create_rfq_on_assigned_request():
    specialist_token = get_valid_sales_specialist_token()
    manager_token = get_valid_sales_manager_token()
    procurement_manager_token = get_valid_procurement_manager_token()
    procurement_specialist_token = get_valid_procurement_specialist_token()
    cod_token = login_as_cod()
    client_id = get_valid_client_id(cod_token)
    supplier_id = get_valid_supplier_id(cod_token)

    create_response = client.post("/requests/", headers=auth_headers(specialist_token), json=create_request_payload(client_id=client_id, title_prefix="specialist_rfq_request", client_ref=unique_value("SPEC-REF")))
    request_id = create_response.json()["id"]
    add_request_items(request_id, specialist_token)
    client.patch(f"/requests/{request_id}/submit", headers=auth_headers(specialist_token))
    client.patch(f"/requests/{request_id}/approve", headers=auth_headers(manager_token), params={"notes": "Approved"})

    specialist_id = client.get("/users/me", headers=auth_headers(procurement_specialist_token)).json()["id"]
    assert client.patch(f"/requests/{request_id}/assign-procurement", headers=auth_headers(procurement_manager_token), params={"assigned_user_id": specialist_id}).status_code == 200

    assert client.post("/rfqs/", headers=auth_headers(procurement_specialist_token), json={"request_id": request_id, "supplier_id": supplier_id, "response_deadline": "2026-12-31T00:00:00"}).status_code == 201


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

    request_id = create_rfq_in_progress_request(specialist_token, manager_token, procurement_manager_token, client_id)
    rfq_id = client.post("/rfqs/", headers=auth_headers(procurement_manager_token), json={"request_id": request_id, "supplier_id": supplier_id, "response_deadline": "2026-12-31T00:00:00"}).json()["id"]
    client.post(f"/rfqs/{rfq_id}/generate-mailto", headers=auth_headers(procurement_manager_token))

    quotation_response = client.post(
        "/quotations/",
        headers=auth_headers(procurement_manager_token),
        json={"rfq_id": rfq_id, "currency": "USD", "subtotal": "45000.00", "total_amount": "46700.00", "payment_terms": "30% advance, 70% on delivery", "delivery_terms": "CIF Tripoli", "lead_time": "6-8 weeks", "validity_date": "2026-06-30T00:00:00", "notes": "Includes warranty 24 months"},
    )
    assert quotation_response.status_code == 201, quotation_response.json()
    quotation_id = quotation_response.json()["id"]
    assert quotation_response.json()["status"] == "received"

    # ---------- Add items to quotation ----------
    quotation_item_response = client.post(
        f"/quotations/{quotation_id}/items",
        headers=auth_headers(procurement_manager_token),
        json={"item_id": client.get(f"/requests/{request_id}/items", headers=auth_headers(procurement_manager_token)).json()[0]["id"], "document_type": "quotation", "document_id": quotation_id, "line_number": 1, "description": "Hydraulic Pump HPU-450", "quantity": 4, "unit": "pcs", "unit_price": "9500.00", "total_price": "38000.00", "currency": "USD", "origin_country": "Germany"},
    )
    assert quotation_item_response.status_code == 201, quotation_item_response.json()
    quotation_line_id = quotation_item_response.json()["id"]

    # ---------- Update quotation item ----------
    update_q_item = client.patch(
        f"/quotations/{quotation_id}/items/{quotation_line_id}",
        headers=auth_headers(procurement_manager_token),
        json={"unit_price": "10000.00", "total_price": "40000.00"},
    )
    assert update_q_item.status_code == 200, update_q_item.json()
    assert update_q_item.json()["unit_price"] is not None

    # ---------- Get quotation items ----------
    q_items = client.get(f"/quotations/{quotation_id}/items", headers=auth_headers(procurement_manager_token))
    assert q_items.status_code == 200
    assert len(q_items.json()) >= 1

    # ---------- Verify RFQ and request status ----------
    assert client.get(f"/rfqs/{rfq_id}", headers=auth_headers(procurement_manager_token)).json()["status"] == "quote_received"
    assert client.get(f"/requests/{request_id}", headers=auth_headers(procurement_manager_token)).json()["status"] == "quotation_review"

    # ---------- Update quotation ----------
    update_q = client.patch(f"/quotations/{quotation_id}", headers=auth_headers(procurement_manager_token), json={"notes": "Updated notes"})
    assert update_q.status_code == 200
    assert update_q.json()["notes"] == "Updated notes"

    # ---------- Cannot add items after submit ----------
    client.patch(f"/quotations/{quotation_id}/submit", headers=auth_headers(procurement_manager_token))

    blocked_item = client.post(
        f"/quotations/{quotation_id}/items",
        headers=auth_headers(procurement_manager_token),
        json={"item_id": client.get(f"/requests/{request_id}/items", headers=auth_headers(procurement_manager_token)).json()[0]["id"], "document_type": "quotation", "document_id": quotation_id, "line_number": 2, "description": "Should not work", "quantity": 1},
    )
    assert blocked_item.status_code == 400, blocked_item.json()

    approve_response = client.patch(f"/quotations/{quotation_id}/approve", headers=auth_headers(procurement_manager_token))
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "selected"
    assert client.get(f"/requests/{request_id}", headers=auth_headers(procurement_manager_token)).json()["status"] == "offer_in_progress"


def test_quotation_reject_and_reopen():
    specialist_token = get_valid_sales_specialist_token()
    manager_token = get_valid_sales_manager_token()
    procurement_manager_token = get_valid_procurement_manager_token()
    cod_token = login_as_cod()
    client_id = get_valid_client_id(cod_token)
    supplier_id = get_valid_supplier_id(cod_token)

    request_id = create_rfq_in_progress_request(specialist_token, manager_token, procurement_manager_token, client_id)
    rfq_id = client.post("/rfqs/", headers=auth_headers(procurement_manager_token), json={"request_id": request_id, "supplier_id": supplier_id, "response_deadline": "2026-12-31T00:00:00"}).json()["id"]
    client.post(f"/rfqs/{rfq_id}/generate-mailto", headers=auth_headers(procurement_manager_token))

    quotation_id = client.post("/quotations/", headers=auth_headers(procurement_manager_token), json={"rfq_id": rfq_id, "currency": "USD", "subtotal": "50000.00", "total_amount": "50000.00", "validity_date": "2026-06-30T00:00:00"}).json()["id"]
    client.patch(f"/quotations/{quotation_id}/submit", headers=auth_headers(procurement_manager_token))

    reject_response = client.patch(f"/quotations/{quotation_id}/reject", headers=auth_headers(procurement_manager_token), params={"rejection_notes": "Price is too high"})
    assert reject_response.status_code == 200
    assert reject_response.json()["status"] == "rejected"
    assert reject_response.json()["rejection_notes"] == "Price is too high"

    reopen_response = client.patch(f"/quotations/{quotation_id}/reopen", headers=auth_headers(procurement_manager_token))
    assert reopen_response.status_code == 200
    assert reopen_response.json()["status"] == "received"
    assert reopen_response.json()["rejection_notes"] is None


def test_quotation_superseded_on_new_submission():
    specialist_token = get_valid_sales_specialist_token()
    manager_token = get_valid_sales_manager_token()
    procurement_manager_token = get_valid_procurement_manager_token()
    cod_token = login_as_cod()
    client_id = get_valid_client_id(cod_token)
    supplier_id = get_valid_supplier_id(cod_token)

    request_id = create_rfq_in_progress_request(specialist_token, manager_token, procurement_manager_token, client_id)
    rfq_id = client.post("/rfqs/", headers=auth_headers(procurement_manager_token), json={"request_id": request_id, "supplier_id": supplier_id, "response_deadline": "2026-12-31T00:00:00"}).json()["id"]
    client.post(f"/rfqs/{rfq_id}/generate-mailto", headers=auth_headers(procurement_manager_token))

    q1_response = client.post("/quotations/", headers=auth_headers(procurement_manager_token), json={"rfq_id": rfq_id, "currency": "USD", "subtotal": "45000.00", "total_amount": "45000.00", "validity_date": "2026-06-30T00:00:00"})
    assert q1_response.status_code == 201
    quotation_id_1 = q1_response.json()["id"]
    assert q1_response.json()["quotation_number"].endswith("-Q1")

    q2_response = client.post("/quotations/", headers=auth_headers(procurement_manager_token), json={"rfq_id": rfq_id, "currency": "USD", "subtotal": "42000.00", "total_amount": "42000.00", "validity_date": "2026-06-30T00:00:00"})
    assert q2_response.status_code == 201
    assert q2_response.json()["quotation_number"].endswith("-Q2")
    assert client.get(f"/quotations/{quotation_id_1}", headers=auth_headers(procurement_manager_token)).json()["status"] == "superseded"


def test_auto_reject_other_quotations_on_submit():
    specialist_token = get_valid_sales_specialist_token()
    manager_token = get_valid_sales_manager_token()
    procurement_manager_token = get_valid_procurement_manager_token()
    cod_token = login_as_cod()
    client_id = get_valid_client_id(cod_token)

    suppliers = client.get("/suppliers/", headers=auth_headers(cod_token)).json()
    assert len(suppliers) >= 2, "Need at least 2 suppliers"
    supplier_id_1 = suppliers[0]["id"]
    supplier_id_2 = suppliers[1]["id"]

    request_id = create_rfq_in_progress_request(specialist_token, manager_token, procurement_manager_token, client_id)
    rfq_id_1 = client.post("/rfqs/", headers=auth_headers(procurement_manager_token), json={"request_id": request_id, "supplier_id": supplier_id_1, "response_deadline": "2026-12-31T00:00:00"}).json()["id"]
    rfq_id_2 = client.post("/rfqs/", headers=auth_headers(procurement_manager_token), json={"request_id": request_id, "supplier_id": supplier_id_2, "response_deadline": "2026-12-31T00:00:00"}).json()["id"]
    client.post(f"/rfqs/{rfq_id_1}/generate-mailto", headers=auth_headers(procurement_manager_token))
    client.post(f"/rfqs/{rfq_id_2}/generate-mailto", headers=auth_headers(procurement_manager_token))

    q1_id = client.post("/quotations/", headers=auth_headers(procurement_manager_token), json={"rfq_id": rfq_id_1, "currency": "USD", "subtotal": "45000.00", "total_amount": "45000.00", "validity_date": "2026-06-30T00:00:00"}).json()["id"]
    q2_id = client.post("/quotations/", headers=auth_headers(procurement_manager_token), json={"rfq_id": rfq_id_2, "currency": "USD", "subtotal": "52000.00", "total_amount": "52000.00", "validity_date": "2026-06-30T00:00:00"}).json()["id"]

    submit_response = client.patch(f"/quotations/{q1_id}/submit", headers=auth_headers(procurement_manager_token))
    assert submit_response.status_code == 200
    assert submit_response.json()["status"] == "under_review"
    assert client.get(f"/quotations/{q2_id}", headers=auth_headers(procurement_manager_token)).json()["status"] == "rejected"


# =====================================================
# OFFER TESTS
# =====================================================

def test_offer_full_flow():
    specialist_token = get_valid_sales_specialist_token()
    manager_token = get_valid_sales_manager_token()
    procurement_manager_token = get_valid_procurement_manager_token()
    cod_token = login_as_cod()
    client_id = get_valid_client_id(cod_token)
    supplier_id = get_valid_supplier_id(cod_token)

    request_id, quotation_id = create_offer_in_progress_request(specialist_token, manager_token, procurement_manager_token, client_id, supplier_id)

    create_offer_response = client.post("/offers/", headers=auth_headers(specialist_token), json={"request_id": request_id, "quotation_id": quotation_id})
    assert create_offer_response.status_code == 201, create_offer_response.json()
    offer_id = create_offer_response.json()["id"]
    assert create_offer_response.json()["current_version"] == 1

    offer_response = client.get(f"/offers/{offer_id}", headers=auth_headers(specialist_token))
    assert offer_response.status_code == 200
    version_id = offer_response.json()["versions"][0]["id"]

    # ---------- Verify items copied from request ----------
    offer_items = client.get(f"/offers/versions/{version_id}/items", headers=auth_headers(specialist_token))
    assert offer_items.status_code == 200
    assert len(offer_items.json()) == 2, "Offer version should have 2 items copied from request"

    # ---------- Update offer version item (add pricing) ----------
    line_id = offer_items.json()[0]["id"]
    update_offer_item = client.patch(
        f"/offers/versions/{version_id}/items/{line_id}",
        headers=auth_headers(specialist_token),
        json={"unit_price": "12000.00", "total_price": "48000.00", "origin_country": "Italy", "warranty": "24 months"},
    )
    assert update_offer_item.status_code == 200, update_offer_item.json()
    assert update_offer_item.json()["origin_country"] == "Italy"

    # ---------- Add a new item to the offer version ----------
    request_items = client.get(f"/requests/{request_id}/items", headers=auth_headers(specialist_token)).json()
    add_offer_item = client.post(
        f"/offers/versions/{version_id}/items",
        headers=auth_headers(specialist_token),
        json={"item_id": request_items[0]["id"], "document_type": "offer_version", "document_id": version_id, "line_number": 3, "description": "Spare Parts Kit", "quantity": 1, "unit": "set"},
    )
    assert add_offer_item.status_code == 201, add_offer_item.json()

    # ---------- Delete the added item ----------
    new_line_id = add_offer_item.json()["id"]
    assert client.delete(f"/offers/versions/{version_id}/items/{new_line_id}", headers=auth_headers(specialist_token)).status_code == 204

    # ---------- Update offer version terms ----------
    update_version = client.patch(
        f"/offers/versions/{version_id}",
        headers=auth_headers(specialist_token),
        json={"payment_terms": "100% upon delivery", "delivery_terms": "DDP", "delivery_period": "16 weeks", "country_of_origin": "Italy"},
    )
    assert update_version.status_code == 200
    assert update_version.json()["payment_terms"] == "100% upon delivery"

    # ---------- Submit for COD approval ----------
    submit_response = client.patch(f"/offers/versions/{version_id}/submit", headers=auth_headers(specialist_token))
    assert submit_response.status_code == 200
    assert submit_response.json()["status"] == "pending_cod_approval"

    # ---------- Cannot modify items after submission ----------
    assert client.patch(f"/offers/versions/{version_id}/items/{line_id}", headers=auth_headers(specialist_token), json={"unit_price": "9999.00"}).status_code == 400

    # ---------- Specialist cannot respond as COD ----------
    assert client.patch(f"/offers/versions/{version_id}/cod-response", headers=auth_headers(specialist_token), json={"cod_status": "approved"}).status_code == 403

    # ---------- COD approves ----------
    cod_response = client.patch(f"/offers/versions/{version_id}/cod-response", headers=auth_headers(cod_token), json={"cod_status": "approved", "cod_notes": None})
    assert cod_response.status_code == 200
    assert cod_response.json()["status"] == "cod_approved"
    assert cod_response.json()["cod_actioned_by_id"] is not None

    # ---------- Send to client ----------
    send_response = client.patch(f"/offers/versions/{version_id}/send", headers=auth_headers(specialist_token))
    assert send_response.status_code == 200
    assert send_response.json()["status"] == "sent_to_client"

    # ---------- Client approves ----------
    client_approve = client.patch(
        f"/offers/versions/{version_id}/client-response",
        headers=auth_headers(specialist_token),
        json={"client_status": "approved", "client_notes": "Agreed on specs"},
    )
    assert client_approve.status_code == 200
    assert client_approve.json()["status"] == "client_approved"

    # ---------- Create version 2 with prices ----------
    new_version = client.post(f"/offers/{offer_id}/new-version", headers=auth_headers(specialist_token))
    assert new_version.status_code == 201
    assert new_version.json()["version_number"] == 2
    version_id_2 = new_version.json()["id"]

    # ---------- Version 2 items copied from version 1 ----------
    v2_items = client.get(f"/offers/versions/{version_id_2}/items", headers=auth_headers(specialist_token))
    assert v2_items.status_code == 200
    assert len(v2_items.json()) == 2, "Version 2 should have items copied from version 1"

    # ---------- Add prices to version 2 items ----------
    v2_line_id = v2_items.json()[0]["id"]
    update_v2_item = client.patch(
        f"/offers/versions/{version_id_2}/items/{v2_line_id}",
        headers=auth_headers(specialist_token),
        json={"unit_price": "15000.00", "total_price": "60000.00"},
    )
    assert update_v2_item.status_code == 200

    assert client.get(f"/offers/{offer_id}", headers=auth_headers(specialist_token)).json()["current_version"] == 2


def test_offer_cod_request_changes():
    specialist_token = get_valid_sales_specialist_token()
    manager_token = get_valid_sales_manager_token()
    procurement_manager_token = get_valid_procurement_manager_token()
    cod_token = login_as_cod()
    client_id = get_valid_client_id(cod_token)
    supplier_id = get_valid_supplier_id(cod_token)

    request_id, quotation_id = create_offer_in_progress_request(specialist_token, manager_token, procurement_manager_token, client_id, supplier_id)
    offer_id = client.post("/offers/", headers=auth_headers(specialist_token), json={"request_id": request_id, "quotation_id": quotation_id}).json()["id"]
    version_id = client.get(f"/offers/{offer_id}", headers=auth_headers(specialist_token)).json()["versions"][0]["id"]

    client.patch(f"/offers/versions/{version_id}/submit", headers=auth_headers(specialist_token))

    changes_response = client.patch(f"/offers/versions/{version_id}/cod-response", headers=auth_headers(cod_token), json={"cod_status": "changes_requested", "cod_notes": "Please add warranty terms"})
    assert changes_response.status_code == 200
    assert changes_response.json()["status"] == "changes_requested"
    assert changes_response.json()["cod_notes"] == "Please add warranty terms"

    # ---------- Can update items after changes_requested ----------
    offer_items = client.get(f"/offers/versions/{version_id}/items", headers=auth_headers(specialist_token)).json()
    if len(offer_items) > 0:
        update_item = client.patch(
            f"/offers/versions/{version_id}/items/{offer_items[0]['id']}",
            headers=auth_headers(specialist_token),
            json={"warranty": "36 months"},
        )
        assert update_item.status_code == 200

    # ---------- Resubmit ----------
    resubmit = client.patch(f"/offers/versions/{version_id}/submit", headers=auth_headers(specialist_token))
    assert resubmit.status_code == 200
    assert resubmit.json()["status"] == "pending_cod_approval"


def test_offer_cod_reject_closes_request():
    specialist_token = get_valid_sales_specialist_token()
    manager_token = get_valid_sales_manager_token()
    procurement_manager_token = get_valid_procurement_manager_token()
    cod_token = login_as_cod()
    client_id = get_valid_client_id(cod_token)
    supplier_id = get_valid_supplier_id(cod_token)

    request_id, quotation_id = create_offer_in_progress_request(specialist_token, manager_token, procurement_manager_token, client_id, supplier_id)
    offer_id = client.post("/offers/", headers=auth_headers(specialist_token), json={"request_id": request_id, "quotation_id": quotation_id}).json()["id"]
    version_id = client.get(f"/offers/{offer_id}", headers=auth_headers(specialist_token)).json()["versions"][0]["id"]

    client.patch(f"/offers/versions/{version_id}/submit", headers=auth_headers(specialist_token))
    reject_response = client.patch(f"/offers/versions/{version_id}/cod-response", headers=auth_headers(cod_token), json={"cod_status": "rejected", "cod_notes": "Does not meet standards"})
    assert reject_response.status_code == 200
    assert reject_response.json()["status"] == "cod_rejected"
    assert client.get(f"/requests/{request_id}", headers=auth_headers(specialist_token)).json()["status"] == "closed"


def test_offer_client_revision_creates_new_version():
    specialist_token = get_valid_sales_specialist_token()
    manager_token = get_valid_sales_manager_token()
    procurement_manager_token = get_valid_procurement_manager_token()
    cod_token = login_as_cod()
    client_id = get_valid_client_id(cod_token)
    supplier_id = get_valid_supplier_id(cod_token)

    request_id, quotation_id = create_offer_in_progress_request(specialist_token, manager_token, procurement_manager_token, client_id, supplier_id)
    offer_id = client.post("/offers/", headers=auth_headers(specialist_token), json={"request_id": request_id, "quotation_id": quotation_id}).json()["id"]
    version_id = client.get(f"/offers/{offer_id}", headers=auth_headers(specialist_token)).json()["versions"][0]["id"]

    client.patch(f"/offers/versions/{version_id}/submit", headers=auth_headers(specialist_token))
    client.patch(f"/offers/versions/{version_id}/cod-response", headers=auth_headers(cod_token), json={"cod_status": "approved"})
    client.patch(f"/offers/versions/{version_id}/send", headers=auth_headers(specialist_token))

    revision_response = client.patch(
        f"/offers/versions/{version_id}/client-response",
        headers=auth_headers(specialist_token),
        json={"client_status": "revision_requested", "client_notes": "Please revise delivery terms"},
    )
    assert revision_response.status_code == 200
    assert revision_response.json()["status"] == "revision_requested"

    new_version = client.post(f"/offers/{offer_id}/new-version", headers=auth_headers(specialist_token))
    assert new_version.status_code == 201
    assert new_version.json()["version_number"] == 2

    # ---------- New version has items copied ----------
    v2_items = client.get(f"/offers/versions/{new_version.json()['id']}/items", headers=auth_headers(specialist_token))
    assert v2_items.status_code == 200
    assert len(v2_items.json()) == 2


def test_offer_client_reject_closes_request():
    specialist_token = get_valid_sales_specialist_token()
    manager_token = get_valid_sales_manager_token()
    procurement_manager_token = get_valid_procurement_manager_token()
    cod_token = login_as_cod()
    client_id = get_valid_client_id(cod_token)
    supplier_id = get_valid_supplier_id(cod_token)

    request_id, quotation_id = create_offer_in_progress_request(specialist_token, manager_token, procurement_manager_token, client_id, supplier_id)
    offer_id = client.post("/offers/", headers=auth_headers(specialist_token), json={"request_id": request_id, "quotation_id": quotation_id}).json()["id"]
    version_id = client.get(f"/offers/{offer_id}", headers=auth_headers(specialist_token)).json()["versions"][0]["id"]

    client.patch(f"/offers/versions/{version_id}/submit", headers=auth_headers(specialist_token))
    client.patch(f"/offers/versions/{version_id}/cod-response", headers=auth_headers(cod_token), json={"cod_status": "approved"})
    client.patch(f"/offers/versions/{version_id}/send", headers=auth_headers(specialist_token))

    reject_response = client.patch(
        f"/offers/versions/{version_id}/client-response",
        headers=auth_headers(specialist_token),
        json={"client_status": "rejected", "client_notes": "Not interested"},
    )
    assert reject_response.status_code == 200
    assert reject_response.json()["status"] == "client_rejected"
    assert client.get(f"/requests/{request_id}", headers=auth_headers(specialist_token)).json()["status"] == "closed"


# =====================================================
# PURCHASE ORDER TESTS
# =====================================================

def test_purchase_order_full_flow():
    specialist_token = get_valid_sales_specialist_token()
    manager_token = get_valid_sales_manager_token()
    procurement_manager_token = get_valid_procurement_manager_token()
    cod_token = login_as_cod()
    client_id = get_valid_client_id(cod_token)
    supplier_id = get_valid_supplier_id(cod_token)

    request_id, quotation_id, version_id = create_approved_by_client_request(
        specialist_token, manager_token, procurement_manager_token, cod_token, client_id, supplier_id
    )

    assert client.get(f"/requests/{request_id}", headers=auth_headers(specialist_token)).json()["status"] == "approved_by_client"

    # ---------- Sales specialist cannot create PO ----------
    assert client.post("/purchase-orders/", headers=auth_headers(specialist_token), json={"offer_version_id": version_id}).status_code == 403

    # ---------- Create PO ----------
    create_po_response = client.post("/purchase-orders/", headers=auth_headers(procurement_manager_token), json={"offer_version_id": version_id})
    assert create_po_response.status_code == 201, create_po_response.json()
    po_data = create_po_response.json()
    po_id = po_data["id"]
    assert po_data["status"] == "draft"
    assert po_data["request_id"] == request_id
    assert po_data["supplier_id"] == supplier_id

    # ---------- Request is now po_in_progress ----------
    assert client.get(f"/requests/{request_id}", headers=auth_headers(procurement_manager_token)).json()["status"] == "po_in_progress"

    # ---------- Get PO ----------
    assert client.get(f"/purchase-orders/{po_id}", headers=auth_headers(procurement_manager_token)).status_code == 200
    assert client.get(f"/purchase-orders/request/{request_id}", headers=auth_headers(procurement_manager_token)).json()["id"] == po_id

    # ---------- Verify items copied from offer version ----------
    po_items = client.get(f"/purchase-orders/{po_id}/items", headers=auth_headers(procurement_manager_token))
    assert po_items.status_code == 200
    assert len(po_items.json()) == 2, "PO should have 2 items copied from offer version"

    # ---------- Update PO item — add unit prices ----------
    po_line_id = po_items.json()[0]["id"]
    update_po_item = client.patch(
        f"/purchase-orders/{po_id}/items/{po_line_id}",
        headers=auth_headers(procurement_manager_token),
        json={"unit_price": "11000.00", "total_price": "44000.00", "currency": "USD"},
    )
    assert update_po_item.status_code == 200, update_po_item.json()
    assert update_po_item.json()["unit_price"] is not None

    # ---------- Update PO terms ----------
    update_po_response = client.patch(
        f"/purchase-orders/{po_id}",
        headers=auth_headers(procurement_manager_token),
        json={"payment_terms": "Updated — 100% upon delivery", "notes": "Updated PO notes"},
    )
    assert update_po_response.status_code == 200
    assert update_po_response.json()["payment_terms"] == "Updated — 100% upon delivery"

    # ---------- Cannot create second PO ----------
    assert client.post("/purchase-orders/", headers=auth_headers(procurement_manager_token), json={"offer_version_id": version_id}).status_code == 400

    # ---------- Send PO ----------
    send_po = client.patch(f"/purchase-orders/{po_id}/send", headers=auth_headers(procurement_manager_token))
    assert send_po.status_code == 200
    assert send_po.json()["status"] == "sent"

    # ---------- Cannot update after sent ----------
    assert client.patch(f"/purchase-orders/{po_id}", headers=auth_headers(procurement_manager_token), json={"notes": "Should not work"}).status_code == 400

    # ---------- Cannot update items after sent ----------
    assert client.patch(f"/purchase-orders/{po_id}/items/{po_line_id}", headers=auth_headers(procurement_manager_token), json={"unit_price": "9999.00"}).status_code == 400

    # ---------- Accept PO ----------
    accept_po = client.patch(f"/purchase-orders/{po_id}/accept", headers=auth_headers(procurement_manager_token))
    assert accept_po.status_code == 200
    assert accept_po.json()["status"] == "accepted"


def test_purchase_order_delete_resets_request():
    specialist_token = get_valid_sales_specialist_token()
    manager_token = get_valid_sales_manager_token()
    procurement_manager_token = get_valid_procurement_manager_token()
    cod_token = login_as_cod()
    client_id = get_valid_client_id(cod_token)
    supplier_id = get_valid_supplier_id(cod_token)

    request_id, quotation_id, version_id = create_approved_by_client_request(
        specialist_token, manager_token, procurement_manager_token, cod_token, client_id, supplier_id
    )

    po_id = client.post("/purchase-orders/", headers=auth_headers(procurement_manager_token), json={"offer_version_id": version_id}).json()["id"]

    # ---------- Verify items on PO ----------
    po_items = client.get(f"/purchase-orders/{po_id}/items", headers=auth_headers(procurement_manager_token))
    assert len(po_items.json()) == 2

    # ---------- Delete PO ----------
    assert client.delete(f"/purchase-orders/{po_id}", headers=auth_headers(procurement_manager_token)).status_code == 204

    # ---------- Request reset to approved_by_client ----------
    assert client.get(f"/requests/{request_id}", headers=auth_headers(procurement_manager_token)).json()["status"] == "approved_by_client"

    # ---------- PO is gone ----------
    assert client.get(f"/purchase-orders/{po_id}", headers=auth_headers(procurement_manager_token)).status_code == 404

    # ---------- Can create new PO ----------
    recreate = client.post("/purchase-orders/", headers=auth_headers(procurement_manager_token), json={"offer_version_id": version_id})
    assert recreate.status_code == 201


# =====================================================
# CLEANUP
# =====================================================

def test_cleanup_test_users():
    cleanup_test_users()