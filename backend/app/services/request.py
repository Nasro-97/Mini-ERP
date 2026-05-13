from datetime import datetime, UTC
from uuid import UUID

from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from app.models import Request, User, Item
from app.schemas import RequestCreate, RequestUpdate, RequestStatus
from app.services.user import get_user_by_id


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
def get_requests(db: Session, current_user: User, status_filter :RequestStatus | None = None) -> list[Request]:
    role_names = [role.name for role in current_user.roles]

    statement = select(Request)

    if "COD" in role_names:
        pass  # sees everything, no filter

    elif "Sales Manager" in role_names:
        statement = statement.where(or_(Request.sales_manager_id == current_user.id,Request.sales_manager_id.is_(None)))


    elif "Procurement Manager" in role_names:

        statement = statement.where( Request.status.in_(PROCUREMENT_VISIBLE_STATUSES)).where(
            or_( Request.procurement_assigned_to_id == current_user.id,Request.procurement_assigned_to_id.is_(None)))


    elif "Procurement Specialist" in role_names:

        statement = statement.where( Request.status.in_(PROCUREMENT_VISIBLE_STATUSES)).where(Request.procurement_assigned_to_id == current_user.id)

    else:
        # Sales Specialist or anyone else
        statement = statement.where( Request.assigned_to_user_id == current_user.id)

    if status_filter:
        statement = statement.where(Request.status == status_filter)


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


# return the request with its items
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
def approve_request(db: Session, request_id: UUID, current_user: User,notes: str | None) -> Request | None:
    request = get_request_by_id(db, request_id)

    if request is None:
        return None

    if request.status != RequestStatus.PENDING_SALES_MANAGER_APPROVAL:
        return None

    request.sales_manager_id = current_user.id
    request.status = RequestStatus.APPROVED_FOR_SOURCING
    request.sales_manager_notes = notes
    request.sales_manager_decision_at = datetime.now(UTC)

    db.commit()
    db.refresh(request)

    return request


def reject_request(db: Session, request_id: UUID,current_user: User, notes: str) -> Request | None:
    request = get_request_by_id(db, request_id)

    if request is None:
        return None

    if request.status != RequestStatus.PENDING_SALES_MANAGER_APPROVAL:
        return None

    request.sales_manager_id = current_user.id
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


# Assigning a procurement user to handle the procurement part of the request
def assign_procurement(db: Session, request_id: UUID, assigned_user_id: UUID, current_user: User) -> Request | None:

    request = get_request_by_id(db, request_id)

    if request is None:
        return None

    if request.status != RequestStatus.APPROVED_FOR_SOURCING:
        return None

    role_names = [role.name for role in current_user.roles]
    if "Procurement Manager" not in  role_names:
        return None

    assigned_user = get_user_by_id(db, assigned_user_id)
    if assigned_user is None:
        return None

    assigned_user_roles = [role.name for role in assigned_user.roles]
    if "Procurement Manager" not in assigned_user_roles and "Procurement Specialist" not in assigned_user_roles:
        return None

    request.procurement_assigned_to_id = assigned_user_id
    request.status = RequestStatus.RFQ_IN_PROGRESS

    db.commit()
    db.refresh(request)
    return request




