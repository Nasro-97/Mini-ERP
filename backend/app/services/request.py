from datetime import datetime, UTC
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models import Request, User, Item
from app.schemas import RequestCreate, RequestUpdate, RequestStatus


PROCUREMENT_VISIBLE_STATUSES = [

    RequestStatus.APPROVED_FOR_SOURCING,
    RequestStatus.RFQ_IN_PROGRESS,
    RequestStatus.QUOTATION_REVIEW,
    RequestStatus.OFFER_IN_PROGRESS,
    RequestStatus.CLIENT_APPROVAL_PENDING,
    RequestStatus.APPROVED_BY_CLIENT,
    RequestStatus.PO_IN_PROGRESS,
    RequestStatus.SHIPMENT_IN_PROGRESS,
    RequestStatus.DELIVERED,
    RequestStatus.CLOSED,
]

# each company have its code
def generate_request_number(db: Session, company_code: str) -> str:
    year_2d = str(datetime.now().year)[2:]   # "26" for 2026
    year_4d = str(datetime.now().year)       # "2026"

    existing_count = db.execute(
        select(func.count()).select_from(Request)
    ).scalar() or 0

    number = str(existing_count + 1).zfill(3)  # "001", "002"

    formats = {
        "company1": f"{year_2d}-{number}",           # 26-001
        "company2": f"QT{year_2d}S{number}",         # QT26S001
        "company3": f"P{year_4d}-{number}",          # P2026-001
        "company4": f"{number}",                     # 001
    }

    return formats.get(company_code, f"REQ-{year_4d}-{number}")

# DRAFT or APPROVED_FOR_SOURCING based on creator role

def create_request(db: Session, request_data: RequestCreate, current_user: User) -> Request:
    #For now this is hardcoded as company 1 but will be updated to use token based on which company is using the database later
    request_number = generate_request_number(db, "company1")

    request = Request(
        request_number= request_number,
        title= request_data.title,
        description= request_data.description,
        client_reference = request_data.client_reference,

        client_id = request_data.client_id,
        created_by_user_id=current_user.id,
        assigned_to_user_id=current_user.id,
        sales_manager_id = request_data.sales_manager_id,

        priority = request_data.priority,

        request_date = request_data.request_date,
        required_date = request_data.required_date,
        deadline = request_data.deadline,

        sales_manager_notes = request_data.sales_manager_notes,
        sales_manager_decision_at = request_data.sales_manager_decision_at
    )

    db.add(request)
    db.commit()

    db.refresh(request)

    return request


def get_request_by_id(db: Session, request_id: UUID) -> Request | None:
    statement = select(Request).where(Request.id == request_id)

    return db.execute(statement).scalar_one_or_none()


# filters by status, client, assigned user
def get_requests(db: Session, current_user: User) -> list[Request]:
    role_names = [role.name for role in current_user.roles]
    statement = select(Request)

    if any(role in role_names for role in ["Sales Manager", "COD"]):
        return list(db.execute(statement).scalars().all())

    if "Procurement Manager" in role_names:
        statement = statement.where(Request.status.in_(PROCUREMENT_VISIBLE_STATUSES))
        return list(db.execute(statement).scalars().all())

    statement = select(Request).where(Request.assigned_to_user_id == current_user.id)
    return list(db.execute(statement).scalars().all())


# general fields only
def update_request(db: Session, request_id: UUID, request_data: RequestUpdate) -> Request | None:
    request = get_request_by_id(db, request_id)

    if request is None: return None

    updated_request = request_data.model_dump(exclude_unset=True)

    for field, value in updated_request.items():
        setattr(request, field, value)

    db.commit()
    db.refresh(request)

    return request

# return the request with it's items
def get_request_with_items(db: Session, request_id: UUID) -> Request | None:
    request = get_request_by_id(db, request_id)

    if request is None:
        return None

    request.items = list(db.execute(
        select(Item).where(Item.request_id == request_id)
    ).scalars().all())

    return request


#   DRAFT -> PENDING_SALES_MANAGER_APPROVAL
def submit_for_review(db: Session, request_id: UUID) -> Request | None:
    request = get_request_by_id(db, request_id)

    if request is None:
        return None

    if request.status != RequestStatus.DRAFT:
        return None  # or raise an exception

    request.status = RequestStatus.PENDING_SALES_MANAGER_APPROVAL

    db.commit()
    db.refresh(request)

    return request


#  PENDING_SALES_MANAGER_APPROVAL ->  APPROVED_FOR_SOURCING
def approve_request(db: Session, request_id: UUID, notes: str | None) -> Request | None:
    request = get_request_by_id(db, request_id)

    if request is None:
        return None

    if request.status != RequestStatus.PENDING_SALES_MANAGER_APPROVAL:
        return None

    request.status = RequestStatus.APPROVED_FOR_SOURCING
    request.sales_manager_notes = notes
    request.sales_manager_decision_at = datetime.now(UTC)

    db.commit()
    db.refresh(request)

    return request


def reject_request(db: Session, request_id: UUID, notes: str) -> Request | None:
    request = get_request_by_id(db, request_id)

    if request is None:
        return None

    if request.status != RequestStatus.PENDING_SALES_MANAGER_APPROVAL:
        return None

    request.status = RequestStatus.REJECTED
    request.sales_manager_notes = notes
    request.sales_manager_decision_at = datetime.now(UTC)

    db.commit()
    db.refresh(request)

    return request


def delete_request(db: Session, request_id: UUID) -> bool:
    request = get_request_by_id(db, request_id)

    if request is None:
        return False

    if request.status != RequestStatus.DRAFT:
        return False  # cannot delete a request already in the workflow

    db.delete(request)
    db.commit()

    return True



