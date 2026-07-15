from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session


from app.core.roles import has_procurement_access
from app.schemas import PurchaseOrderCreate, PurchaseOrderUpdate
from app.models import PurchaseOrder, User, RequestStatus, POStatus, DocumentType

from app.services.request import get_request_by_id
from app.services.offer import get_offer_by_id, get_offer_version_by_id
from app.services.quotation import get_quotation_by_id
from app.services.document_item import copy_document_items
from app.services.document_counter import generate_document_number


def create_po(db: Session, po_data: PurchaseOrderCreate, current_user: User) -> PurchaseOrder | None:
    # FOR NOW ONLY COMPANY 1 Later the frontend will send it
    po_number = generate_document_number(db, "po", "company1")

    offer_version = get_offer_version_by_id(db, po_data.offer_version_id)
    if offer_version is None: return None

    offer = get_offer_by_id(db, offer_version.offer_id)
    if offer is None: return None

    request = get_request_by_id(db, offer.request_id)
    if request is None: return None

    if request.status != RequestStatus.APPROVED_BY_CLIENT: return None

    quotation = get_quotation_by_id(db, offer.quotation_id)
    if quotation is None: return None

    is_assigned = request.procurement_assigned_to_id == current_user.id

    if not has_procurement_access(current_user) and not is_assigned:
        return None

    existing_purchase_order = db.execute(select(PurchaseOrder).where(
        PurchaseOrder.request_id == request.id)).scalar_one_or_none()
    if existing_purchase_order is not None: return None

    purchase_order = PurchaseOrder(
        offer_version_id=offer_version.id,
        request_id = request.id,
        quotation_id = quotation.id,
        supplier_id = quotation.supplier_id,
        created_by_user_id = current_user.id,

        po_number = po_number,
        status = POStatus.DRAFT,

        payment_terms = quotation.payment_terms,
        delivery_terms = quotation.delivery_terms,
        lead_time = quotation.lead_time,

        notes = quotation.notes,

        currency = quotation.currency,
        subtotal = quotation.subtotal,
        shipping_cost = quotation.shipping_cost,
        taxes = quotation.taxes,
        other_costs = quotation.other_costs,
        total_amount = quotation.total_amount,
    )

    request.status = RequestStatus.PO_IN_PROGRESS

    db.add(purchase_order)
    db.flush()

    copy_document_items(
        db,
        source_type=DocumentType.OFFER_VERSION,
        source_id=offer_version.id,
        target_type=DocumentType.PURCHASE_ORDER,
        target_id=purchase_order.id,
    )

    db.commit()
    db.refresh(purchase_order)

    return purchase_order


def get_po_by_id(db: Session, po_id: UUID) -> PurchaseOrder | None:
    statement = db.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    return statement.scalar_one_or_none()


def get_po_by_request(db: Session, request_id: UUID) -> PurchaseOrder | None:
    statement = db.execute(select(PurchaseOrder).where(PurchaseOrder.request_id == request_id))
    return statement.scalar_one_or_none()


def update_po(db: Session,po_id: UUID, po_data: PurchaseOrderUpdate, current_user: User) -> PurchaseOrder | None:
    purchase_order = get_po_by_id(db, po_id)
    if purchase_order is None: return None

    if purchase_order.status != POStatus.DRAFT:
        return None

    request = get_request_by_id(db, purchase_order.request_id)
    if request is None:
        return None

    is_assigned = request.procurement_assigned_to_id == current_user.id
    if not has_procurement_access(current_user) and not is_assigned:
        return None

    updated_po = po_data.model_dump(exclude_unset=True)

    for field, value in updated_po.items():
        setattr(purchase_order, field, value)

    db.commit()
    db.refresh(purchase_order)

    return purchase_order

def send_po(db: Session, po_id: UUID, current_user: User) -> PurchaseOrder | None:
    purchase_order = get_po_by_id(db, po_id)
    if purchase_order is None: return None

    request = get_request_by_id(db, purchase_order.request_id)
    if request is None:
        return None

    if purchase_order.status != POStatus.DRAFT:
        return None

    is_assigned = request.procurement_assigned_to_id == current_user.id
    if not has_procurement_access(current_user) and not is_assigned:
        return None

    purchase_order.status = POStatus.SENT
    db.commit()
    db.refresh(purchase_order)

    return purchase_order

def accept_po(db: Session, po_id: UUID, current_user: User) -> PurchaseOrder | None:
    purchase_order = get_po_by_id(db, po_id)
    if purchase_order is None: return None

    request = get_request_by_id(db, purchase_order.request_id)
    if request is None:
        return None

    if purchase_order.status != POStatus.SENT:
        return None

    is_assigned = request.procurement_assigned_to_id == current_user.id
    if not has_procurement_access(current_user) and not is_assigned:
        return None

    purchase_order.status = POStatus.ACCEPTED

    request.status = RequestStatus.SHIPMENT_IN_PROGRESS

    db.commit()
    db.refresh(purchase_order)

    return purchase_order


def request_po_changes(db: Session, po_id: UUID, current_user: User) -> PurchaseOrder | None:
    purchase_order = get_po_by_id(db, po_id)
    if purchase_order is None:
        return None

    request = get_request_by_id(db, purchase_order.request_id)
    if request is None:
        return None

    if purchase_order.status != POStatus.SENT:
        return None

    is_assigned = request.procurement_assigned_to_id == current_user.id
    if not has_procurement_access(current_user) and not is_assigned:
        return None

    purchase_order.status = POStatus.DRAFT

    db.commit()
    db.refresh(purchase_order)

    return purchase_order


def delete_po(db: Session, po_id: UUID, current_user: User) -> bool:
    purchase_order = get_po_by_id(db, po_id)
    if purchase_order is None:
        return False

    request = get_request_by_id(db, purchase_order.request_id)
    if request is None:
        return False

    if purchase_order.status != POStatus.DRAFT:
        return False

    is_assigned = request.procurement_assigned_to_id == current_user.id
    if not has_procurement_access(current_user) and not is_assigned:
        return False

    request.status = RequestStatus.APPROVED_BY_CLIENT

    db.delete(purchase_order)
    db.commit()

    return True

