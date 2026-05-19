from datetime import datetime, UTC
from uuid import UUID

from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from app.models import Request, User, Item
from app.schemas.request import RequestCreate, RequestUpdate, RequestStatus
from app.services.user import get_user_by_id
from app.core.roles import (
    is_cod,
    is_sales_manager,
    is_procurement_manager,
    is_procurement_specialist,
    has_sales_management_access,
    has_procurement_access,
)


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


def generate_request_number(db: Session, company_code: str) -> str:
    year_2d = str(datetime.now().year)[2:]
    year_4d = str(datetime.now().year)

    existing_count = db.execute(select(func.count()).select_from(Request)).scalar() or 0
    number = str(existing_count + 1).zfill(3)

    formats = {
        "company1": f"{year_2d}-{number}",
        "company2": f"QT{year_2d}S{number}",
        "company3": f"P{year_4d}-{number}",
        "company4": f"{number}",
    }

    return formats.get(company_code, f"REQ-{year_4d}-{number}")


def create_request(db: Session, request_data: RequestCreate, current_user: User) -> Request:
    request_number = generate_request_number(db, "company1")

    request = Request(
        request_number=request_number,
        title=request_data.title,
        description=request_data.description,
        client_reference=request_data.client_reference,
        client_id=request_data.client_id,
        created_by_user_id=current_user.id,
        assigned_to_user_id=current_user.id,
        priority=request_data.priority,
        request_date=request_data.request_date,
        required_date=request_data.required_date,
        deadline=request_data.deadline,
        sales_manager_notes=request_data.sales_manager_notes,
        sales_manager_decision_at=request_data.sales_manager_decision_at,
    )

    db.add(request)
    db.commit()
    db.refresh(request)

    return request


def get_request_by_id(db: Session, request_id: UUID) -> Request | None:
    statement = select(Request).where(Request.id == request_id)
    return db.execute(statement).scalar_one_or_none()


def get_requests(db: Session, current_user: User, status_filter: RequestStatus | None = None) -> list[Request]:
    statement = select(Request)

    if is_cod(current_user):
        pass

    elif is_sales_manager(current_user):
        statement = statement.where(
            or_(
                Request.sales_manager_id == current_user.id,
                Request.sales_manager_id.is_(None)
            )
        )

    elif is_procurement_manager(current_user):
        statement = statement.where(
            Request.status.in_(PROCUREMENT_VISIBLE_STATUSES)
        )

    elif is_procurement_specialist(current_user):
        statement = statement.where(
            Request.status.in_(PROCUREMENT_VISIBLE_STATUSES)
        ).where(
            Request.procurement_assigned_to_id == current_user.id
        )

    else:
        statement = statement.where(
            Request.assigned_to_user_id == current_user.id
        )

    if status_filter:
        statement = statement.where(Request.status == status_filter)

    return list(db.execute(statement).scalars().all())


def get_request_with_items(db: Session, request_id: UUID) -> Request | None:
    request = get_request_by_id(db, request_id)

    if request is None:
        return None

    request.items = list(db.execute(
        select(Item).where(Item.request_id == request_id)
    ).scalars().all())

    return request


def update_request(db: Session, request_id: UUID, request_data: RequestUpdate) -> Request | None:
    request = get_request_by_id(db, request_id)

    if request is None:
        return None

    updated_request = request_data.model_dump(exclude_unset=True)

    for field, value in updated_request.items():
        setattr(request, field, value)

    db.commit()
    db.refresh(request)

    return request


def submit_for_review(db: Session, request_id: UUID) -> Request | None:
    request = get_request_by_id(db, request_id)

    if request is None:
        return None

    if request.status != RequestStatus.DRAFT:
        return None

    request.status = RequestStatus.PENDING_SALES_MANAGER_APPROVAL

    db.commit()
    db.refresh(request)

    return request


def approve_request(db: Session, request_id: UUID, current_user: User, notes: str | None) -> Request | None:
    request = get_request_by_id(db, request_id)

    if request is None:
        return None

    if request.status != RequestStatus.PENDING_SALES_MANAGER_APPROVAL:
        return None

    if not has_sales_management_access(current_user):
        return None

    request.sales_manager_id = current_user.id
    request.status = RequestStatus.APPROVED_FOR_SOURCING
    request.sales_manager_notes = notes
    request.sales_manager_decision_at = datetime.now(UTC)

    db.commit()
    db.refresh(request)

    return request


def reject_request(db: Session, request_id: UUID, current_user: User, notes: str) -> Request | None:
    request = get_request_by_id(db, request_id)

    if request is None:
        return None

    if request.status != RequestStatus.PENDING_SALES_MANAGER_APPROVAL:
        return None

    if not has_sales_management_access(current_user):
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
        return False

    db.delete(request)
    db.commit()

    return True


def assign_procurement(db: Session, request_id: UUID, assigned_user_id: UUID, current_user: User) -> Request | None:
    request = get_request_by_id(db, request_id)

    if request is None:
        return None

    if request.status != RequestStatus.APPROVED_FOR_SOURCING:
        return None

    if not has_procurement_access(current_user):
        return None

    assigned_user = get_user_by_id(db, assigned_user_id)

    if assigned_user is None:
        return None

    if not is_procurement_manager(assigned_user) and not is_procurement_specialist(assigned_user):
        return None

    request.procurement_assigned_to_id = assigned_user_id
    request.status = RequestStatus.RFQ_IN_PROGRESS

    db.commit()
    db.refresh(request)

    return request