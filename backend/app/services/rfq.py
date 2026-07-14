from uuid import UUID
from datetime import datetime, UTC
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.roles import has_procurement_access
from app.models import RFQ, RFQStatus, RequestStatus, User, Supplier, Contact
from app.schemas import RFQCreate, RFQUpdate
from app.services.request import get_request_by_id


def create_rfq(db: Session, rfq_data: RFQCreate, current_user: User) -> RFQ | None:

    request = get_request_by_id(db, rfq_data.request_id)
    if request is None:
        return None

    if request.status != RequestStatus.RFQ_IN_PROGRESS and request.status != RequestStatus.QUOTATION_REVIEW:
        return None

    is_assigned = request.procurement_assigned_to_id == current_user.id

    if not has_procurement_access(current_user) and not is_assigned:
        return None

    supplier = db.execute(
        select(Supplier).where(Supplier.id == rfq_data.supplier_id)
    ).scalar_one_or_none()

    if supplier is None:
        return None

    if rfq_data.contact_id is not None:
        contact = db.execute(
            select(Contact).where(
                Contact.id == rfq_data.contact_id,
                Contact.company_id == rfq_data.supplier_id
            )
        ).scalar_one_or_none()
        if contact is None:
            return None

    existing_count = db.execute(
        select(func.count()).select_from(RFQ).where(RFQ.request_id == request.id)
    ).scalar() or 0

    rfq_number = f"{request.request_number}-RFQ-{existing_count + 1}"

    rfq = RFQ(
        request_id=rfq_data.request_id,
        supplier_id=rfq_data.supplier_id,
        contact_id=rfq_data.contact_id,
        procurement_manager_id=current_user.id,
        rfq_number=rfq_number,
        status=RFQStatus.DRAFT,
        notes=rfq_data.notes,
        response_deadline=rfq_data.response_deadline,
    )

    db.add(rfq)
    db.commit()
    db.refresh(rfq)

    return rfq


def get_rfq_by_id(db: Session, rfq_id: UUID) -> RFQ | None:
    statement = select(RFQ).where(RFQ.id == rfq_id)
    return db.execute(statement).scalar_one_or_none()


def get_rfqs_by_supplier(db: Session, supplier_id: UUID) -> RFQ | None:
    statement = select(RFQ).where(RFQ.supplier_id == supplier_id)
    return db.execute(statement).scalars().all()


def get_rfqs_by_request(db: Session, request_id: UUID) -> list[RFQ]:
    statement = select(RFQ).where(RFQ.request_id == request_id)
    return list(db.execute(statement).scalars().all())


def update_rfq(db: Session, rfq_id: UUID, rfq_data: RFQUpdate, current_user: User) -> RFQ | None:
    rfq = get_rfq_by_id(db, rfq_id)
    if rfq is None:
        return None

    request = get_request_by_id(db, rfq.request_id)
    if request is None:
        return None

    is_assigned = request.procurement_assigned_to_id == current_user.id

    if not has_procurement_access(current_user) and not is_assigned:
        return None

    if rfq.status != RFQStatus.DRAFT:
        return None

    updated_rfq = rfq_data.model_dump(exclude_unset=True)

    for field, value in updated_rfq.items():
        setattr(rfq, field, value)

    db.commit()
    db.refresh(rfq)

    return rfq


def generate_mailto(db: Session, rfq_id: UUID, current_user: User) -> dict | None:
    rfq = get_rfq_by_id(db, rfq_id)
    if rfq is None:
        return None

    if rfq.status not in [RFQStatus.DRAFT, RFQStatus.SENT]:
        return None

    request = get_request_by_id(db, rfq.request_id)
    if request is None:
        return None

    is_assigned = request.procurement_assigned_to_id == current_user.id
    if not has_procurement_access(current_user) and not is_assigned:
        return None

    supplier = db.execute(
        select(Supplier).where(Supplier.id == rfq.supplier_id)
    ).scalar_one_or_none()
    if supplier is None:
        return None

    if rfq.contact_id is not None:
        contact = db.execute(
            select(Contact).where(Contact.id == rfq.contact_id)
        ).scalar_one_or_none()
        to_email = contact.email if contact and contact.email else supplier.email
        to_name = contact.fullname if contact else supplier.company_name
    else:
        to_email = supplier.email
        to_name = supplier.company_name

    subject = settings.RFQ_EMAIL_SUBJECT.format(
        request_number=request.request_number
    )

    body = (
        f"{settings.RFQ_EMAIL_GREETING.format(to_name=to_name)}\n\n"
        f"{settings.RFQ_EMAIL_INTRO}\n\n"
        f"RFQ Reference: {rfq.rfq_number}\n"
        f"Response Deadline: {rfq.response_deadline.strftime('%d %B %Y')}\n\n"
        f"{settings.RFQ_EMAIL_REQUIREMENTS}\n\n"
    )

    if rfq.notes:
        body += f"Additional notes:\n{rfq.notes}\n\n"

    body += (
        f"{settings.RFQ_EMAIL_CLOSING}\n"
        f"{current_user.fullname}\n"
        f"{settings.COMPANY_NAME}\n"
        f"{settings.COMPANY_EMAIL}\n"
        f"{settings.COMPANY_PHONE}"
    )


    return {
        "to": to_email,
        "cc": settings.COMPANY_EMAIL,
        "subject": subject,
        "body": body,
        "rfq_number": rfq.rfq_number,
    }


def mark_rfq_as_sent(db: Session, rfq_id: UUID, current_user: User) -> RFQ | None:
    rfq = get_rfq_by_id(db, rfq_id)
    if rfq is None:
        return None

    if rfq.status != RFQStatus.DRAFT:
        return None

    request = get_request_by_id(db, rfq.request_id)
    if request is None:
        return None

    is_assigned = request.procurement_assigned_to_id == current_user.id
    if not has_procurement_access(current_user) and not is_assigned:
        return None

    rfq.status = RFQStatus.SENT
    rfq.sent_at = datetime.now(UTC)

    db.commit()
    db.refresh(rfq)
    return rfq


def decline_rfq(db: Session, rfq_id: UUID, current_user: User) -> RFQ | None:
    rfq = get_rfq_by_id(db, rfq_id)
    if rfq is None:
        return None

    if rfq.status != RFQStatus.SENT:
        return None

    request = get_request_by_id(db, rfq.request_id)
    if request is None:
        return None

    is_assigned = request.procurement_assigned_to_id == current_user.id

    if not has_procurement_access(current_user) and not is_assigned:
        return None

    rfq.status = RFQStatus.DECLINED
    db.flush()

    _check_and_update_request_status(db, rfq.request_id)

    db.commit()
    db.refresh(rfq)

    return rfq


def delete_rfq(db: Session, rfq_id: UUID) -> bool:
    rfq = get_rfq_by_id(db, rfq_id)
    if rfq is None:
        return False

    if rfq.status != RFQStatus.DRAFT:
        return False

    db.delete(rfq)
    db.commit()

    return True


def _check_and_update_request_status(db: Session, request_id: UUID) -> None:
    request = get_request_by_id(db, request_id)
    if request is None:
        return

    all_rfqs = db.execute(
        select(RFQ).where(RFQ.request_id == request_id)
    ).scalars().all()

    if not all_rfqs:
        return

    all_resolved = all(
        r.status in [RFQStatus.DECLINED, RFQStatus.QUOTE_RECEIVED]
        for r in all_rfqs
    )

    if all_resolved:
        any_quote_received = any(
            r.status == RFQStatus.QUOTE_RECEIVED
            for r in all_rfqs
        )
        if any_quote_received:
            request.status = RequestStatus.QUOTATION_REVIEW
        else:
            request.status = RequestStatus.CLOSED