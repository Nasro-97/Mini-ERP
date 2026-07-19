from uuid import UUID
from datetime import datetime, UTC
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.company_database import company_code
from app.core.roles import has_procurement_access
from app.models import Quotation, QuotationStatus, User, RFQStatus, RequestStatus
from app.schemas import QuotationCreate, QuotationUpdate
from app.services.rfq import get_rfq_by_id, _check_and_update_request_status, get_rfqs_by_request
from app.services.request import get_request_by_id
from app.services.document_counter import generate_document_number

# create_quotation — get the RFQ first, copy supplier_id from it, change RFQ status to QUOTE_RECEIVED, then call _check_and_update_request_status from the RFQ service.
def create_quotation(db: Session, quotation_data: QuotationCreate, current_user: User) -> Quotation| None:
    rfq = get_rfq_by_id(db, quotation_data.rfq_id)
    if not rfq: return None

    request = get_request_by_id(db, rfq.request_id)
    if request is None:
        return None

    is_assigned = request.procurement_assigned_to_id == current_user.id

    if not has_procurement_access(current_user) and not is_assigned:
        return None

    # supersede any existing quotation for this RFQ
    existing_quotation = db.execute(select(Quotation).where(Quotation.rfq_id == rfq.id)).scalars().all()
    for q in existing_quotation:
        if q.status not in [QuotationStatus.REJECTED, QuotationStatus.SUPERSEDED]:
            q.status = QuotationStatus.SUPERSEDED

    existing_count = db.execute(
        select(func.count()).select_from(Quotation).where(Quotation.rfq_id == rfq.id)
    ).scalar() or 0

    company_code = db.info["company_code"]
    quotation_number = generate_document_number(db, "quotation", company_code)


    quotation = Quotation(
        rfq_id=rfq.id,
        supplier_id=rfq.supplier_id,
        quotation_number=quotation_number,
        supplier_reference= quotation_data.supplier_reference,
        currency= quotation_data.currency,
        subtotal= quotation_data.subtotal,
        shipping_cost= quotation_data.shipping_cost,
        taxes= quotation_data.taxes,
        other_costs= quotation_data.other_costs,
        total_amount= quotation_data.total_amount,
        payment_terms= quotation_data.payment_terms,
        delivery_terms= quotation_data.delivery_terms,
        lead_time= quotation_data.lead_time,
        validity_date= quotation_data.validity_date,
        notes= quotation_data.notes,
    )

    db.add(quotation)

    rfq.status = RFQStatus.QUOTE_RECEIVED
    db.flush()
    _check_and_update_request_status(db, rfq.request_id)

    db.commit()
    db.refresh(quotation)

    return quotation


def get_quotation_by_id(db: Session, quotation_id: UUID) -> Quotation | None:
    statement = select(Quotation).where(Quotation.id == quotation_id)

    return db.execute(statement).scalar_one_or_none()


# submit_for_review — query all RFQs for the request, collect their ids, reject all other RECEIVED quotations across those RFQ ids.
def submit_for_review(db: Session, quotation_id, current_user: User) -> Quotation | None:
    quotation = get_quotation_by_id(db, quotation_id)

    if not quotation:
        return None

    if quotation.status != QuotationStatus.RECEIVED:
        return None

    rfq = get_rfq_by_id(db, quotation.rfq_id)
    if not rfq:
        return None

    request = get_request_by_id(db, rfq.request_id)
    if not request:
        return None

    is_assigned = request.procurement_assigned_to_id == current_user.id

    if not has_procurement_access(current_user) and not is_assigned:
        return None

    all_rfqs= get_rfqs_by_request(db, rfq.request_id)
    all_rfq_ids = [rfq.id for rfq in all_rfqs]

    statement = select(Quotation).where( Quotation.rfq_id.in_(all_rfq_ids),
                                        Quotation.id != quotation_id,
                                        Quotation.status == QuotationStatus.RECEIVED
                                        )
    other_quotation = db.execute(statement).scalars().all()

    for q in other_quotation:
        q.status = QuotationStatus.REJECTED

    quotation.status = QuotationStatus.UNDER_REVIEW
    quotation.submitted_for_review_at = datetime.now(UTC)

    
    db.commit()
    db.refresh(quotation)
    return quotation


def update_quotation(db: Session, quotation_id: UUID, quotation_data: QuotationUpdate, current_user: User) -> Quotation | None:
    quotation = get_quotation_by_id(db, quotation_id)
    if quotation is None:
        return None

    if quotation.status != QuotationStatus.RECEIVED:
        return None

    rfq = get_rfq_by_id(db, quotation.rfq_id)
    if rfq is None:
        return None

    request = get_request_by_id(db, rfq.request_id)
    if request is None:
        return None

    is_assigned = request.procurement_assigned_to_id == current_user.id

    if not has_procurement_access(current_user) and not is_assigned:
        return None

    updated_data = quotation_data.model_dump(exclude_unset=True)

    for field, value in updated_data.items():
        setattr(quotation, field, value)

    db.commit()
    db.refresh(quotation)

    return quotation


# approve_quotation — only has_procurement_access, changes request to OFFER_IN_PROGRESS.
def approve_quotation(db: Session, quotation_id: UUID, current_user: User) -> Quotation | None:
    quotation = get_quotation_by_id(db, quotation_id)

    if not quotation:
        return None
    if quotation.status != QuotationStatus.UNDER_REVIEW:
        return None
    if not has_procurement_access(current_user):
        return None

    rfq = get_rfq_by_id(db, quotation.rfq_id)
    if rfq is None:
        return None
    request = get_request_by_id(db, rfq.request_id)
    if request is None:
        return None

    quotation.status = QuotationStatus.SELECTED
    request.status = RequestStatus.OFFER_IN_PROGRESS

    db.commit()
    db.refresh(quotation)

    return quotation


# reject_quotation — only has_procurement_access, requires rejection_notes, goes back to REJECTED.
def reject_quotation(db: Session, quotation_id: UUID, rejection_notes: str, current_user: User) -> Quotation | None:
    quotation = get_quotation_by_id(db, quotation_id)

    if not quotation:
        return None
    if quotation.status != QuotationStatus.UNDER_REVIEW:
        return None
    if not has_procurement_access(current_user):
        return None

    rfq = get_rfq_by_id(db, quotation.rfq_id)
    if rfq is None:
        return None
    request = get_request_by_id(db, rfq.request_id)
    if request is None:
        return None

    quotation.status = QuotationStatus.REJECTED
    quotation.rejection_notes = rejection_notes

    db.commit()
    db.refresh(quotation)

    return quotation


# reopen_quotation — has_procurement_access or assigned user, clears rejection_notes.
def reopen_quotation(db:Session, quotation_id: UUID, current_user: User) -> Quotation | None:
    quotation = get_quotation_by_id(db, quotation_id)
    if quotation is None:
        return None

    if quotation.status != QuotationStatus.REJECTED:
        return None

    rfq = get_rfq_by_id(db, quotation.rfq_id)
    if rfq is None:
        return None

    request = get_request_by_id(db, rfq.request_id)
    if request is None:
        return None

    is_assigned = request.procurement_assigned_to_id == current_user.id

    if not has_procurement_access(current_user) and not is_assigned:
        return None

    quotation.status = QuotationStatus.RECEIVED
    quotation.rejection_notes = None

    db.commit()
    db.refresh(quotation)

    return quotation


def get_quotations_by_rfq(db: Session, rfq_id: UUID) -> list[Quotation]:
    statement = select(Quotation).where(Quotation.rfq_id == rfq_id)
    return list(db.execute(statement).scalars().all())