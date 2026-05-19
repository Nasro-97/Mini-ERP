from uuid import UUID
from datetime import datetime, UTC
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.roles import has_sales_management_access, is_cod

from app.services.quotation import get_quotation_by_id
from app.services.request import get_request_by_id
from app.services.document_item import copy_items_from_request, copy_document_items

from app.schemas import OfferCreate, OfferVersionUpdate, ClientResponseSchema, CodResponseSchema
from app.models import Offer, OfferStatus, User, RequestStatus, OfferVersion, DocumentType


# create offer → creates offer + first version + copies item lines from request
def create_offer(db: Session, offer_data: OfferCreate, current_user: User) -> Offer | None:
    request = get_request_by_id(db, offer_data.request_id)
    if request is None: return None

    if request.status != RequestStatus.OFFER_IN_PROGRESS:
        return None

    quotation = get_quotation_by_id(db, offer_data.quotation_id)
    if quotation is None: return None

    existing_offer = db.execute(select(Offer).where(Offer.request_id == offer_data.request_id)).scalars().one_or_none()
    if existing_offer is not None: return None

    is_assigned = request.assigned_to_user_id == current_user.id
    if not has_sales_management_access(current_user) and not is_assigned:
        return None

    offer = Offer(
        request_id = request.id,
        quotation_id = quotation.id,
        created_by_user_id=current_user.id,
        offer_number=request.request_number,
        current_version=1,
    )

    db.add(offer)
    db.flush()

    version = OfferVersion(
        offer_id=offer.id,
        version_number=1,
        status=OfferStatus.DRAFT,
    )

    db.add(version)
    db.flush()

    copy_items_from_request(db, request.id, version.id)

    db.commit()
    db.refresh(offer)



    return offer


def get_offer_by_id(db: Session, offer_id: UUID) -> Offer | None:
    statement = select(Offer).where(Offer.id == offer_id)
    return db.execute(statement).scalar_one_or_none()


def get_offer_with_versions(db: Session, offer_id: UUID) -> Offer | None:
    offer = get_offer_by_id(db, offer_id)
    if offer is None: return None

    offer.versions = list(db.execute( select(OfferVersion).where(OfferVersion.offer_id == offer_id).order_by(OfferVersion.version_number)).scalars().all())

    return offer


def get_offer_by_request(db: Session, request_id: UUID) -> Offer | None:
    statement = select(Offer).where(Offer.request_id == request_id)
    offer = db.execute(statement).scalar_one_or_none()
    if offer is None:
        return None

    offer.versions = list(db.execute( select(OfferVersion).where(OfferVersion.offer_id == offer.id).order_by(OfferVersion.version_number)).scalars().all())

    return offer


def get_offer_version_by_id(db: Session, offer_version_id: UUID) -> OfferVersion | None:
    statement = select(OfferVersion).where(OfferVersion.id == offer_version_id)
    return db.execute(statement).scalar_one_or_none()


def update_offer_version(db: Session, offer_version_id: UUID , offer_version_data: OfferVersionUpdate) -> OfferVersion | None:
    offer_version = get_offer_version_by_id(db, offer_version_id)

    if offer_version is None:
        return None

    if offer_version.status not in [OfferStatus.DRAFT,OfferStatus.CHANGES_REQUESTED]:
        return None

    updated_data = offer_version_data.model_dump(exclude_unset=True)

    for field, value in updated_data.items():
        setattr(offer_version, field, value)

    db.commit()
    db.refresh(offer_version)

    return offer_version


def submit_for_cod_approval(db: Session, offer_version_id: UUID, current_user: User) -> OfferVersion | None:
    offer_version = get_offer_version_by_id(db, offer_version_id)
    if offer_version is None:
        return None

    offer_data = get_offer_by_id(db, offer_version.offer_id)
    if offer_data is None: return None

    request = get_request_by_id(db, offer_data.request_id)
    if request is None: return None

    is_assigned = request.assigned_to_user_id == current_user.id

    if not has_sales_management_access(current_user) and not is_assigned:
        return None

    if offer_version.status not in [OfferStatus.DRAFT,OfferStatus.CHANGES_REQUESTED]:
        return None

    offer_version.status = OfferStatus.PENDING_COD_APPROVAL

    db.commit()
    db.refresh(offer_version)

    return offer_version


def record_cod_response( db: Session, offer_version_id: UUID, cod_response: CodResponseSchema, current_user: User) -> OfferVersion | None:

    offer_version = get_offer_version_by_id(db, offer_version_id)
    if offer_version is None:
        return None

    if not is_cod(current_user):
        return None

    if offer_version.status != OfferStatus.PENDING_COD_APPROVAL:
        return None

    offer_version.cod_notes = cod_response.cod_notes
    cod_status = cod_response.cod_status
    offer_version.cod_actioned_by_id = current_user.id
    offer_version.cod_actioned_at = datetime.now(UTC)

    if cod_status == "approved":
        offer_version.status = OfferStatus.COD_APPROVED
        offer_version.cod_actioned_by_id_by_id = current_user.id
        offer_version.cod_actioned_at = datetime.now(UTC)

    elif cod_status == "rejected":
        offer_version.status = OfferStatus.COD_REJECTED
        offer_version.cod_actioned_by_id = current_user.id
        offer_version.cod_actioned_at = datetime.now(UTC)

        offer = get_offer_by_id(db, offer_version.offer_id)
        if offer is None:
            return None

        request = get_request_by_id(db, offer.request_id)
        if request is None:
            return None

        request.status = RequestStatus.CLOSED

    elif cod_status == "changes_requested":
        offer_version.status = OfferStatus.CHANGES_REQUESTED
        offer_version.cod_actioned_by_id = current_user.id
        offer_version.cod_actioned_at = datetime.now(UTC)

    else:
        return None

    db.commit()
    db.refresh(offer_version)

    return offer_version


def send_to_client(db: Session, offer_version_id: UUID, current_user: User):

    offer_version = get_offer_version_by_id(db, offer_version_id)
    if offer_version is None:
        return None

    offer = get_offer_by_id(db, offer_version.offer_id)
    if offer is None: return None
    request = get_request_by_id(db, offer.request_id)
    if request is None: return None

    is_assigned = request.assigned_to_user_id == current_user.id

    if not has_sales_management_access(current_user) and not is_assigned:
        return None

    if offer_version.status != OfferStatus.COD_APPROVED:
        return None

    offer_version.status = OfferStatus.SENT_TO_CLIENT

    db.commit()
    db.refresh(offer_version)

    return offer_version


def record_client_response(db: Session, offer_version_id: UUID, client_response: ClientResponseSchema, current_user: User) -> OfferVersion | None:
    offer_version = get_offer_version_by_id(db, offer_version_id)
    if offer_version is None:
        return None

    if offer_version.status != OfferStatus.SENT_TO_CLIENT:
        return None

    offer = get_offer_by_id(db, offer_version.offer_id)
    if offer is None:
        return None

    request = get_request_by_id(db, offer.request_id)
    if request is None:
        return None

    is_assigned = request.assigned_to_user_id == current_user.id

    if not has_sales_management_access(current_user) and not is_assigned:
        return None

    from datetime import datetime, UTC
    offer_version.client_notes = client_response.client_notes
    offer_version.client_responded_at = datetime.now(UTC)

    if client_response.client_status == "approved":
        offer_version.status = OfferStatus.CLIENT_APPROVED
        request.status = RequestStatus.APPROVED_BY_CLIENT

    elif client_response.client_status == "rejected":
        offer_version.status = OfferStatus.CLIENT_REJECTED
        request.status = RequestStatus.CLOSED

    elif client_response.client_status == "revision_requested":
        offer_version.status = OfferStatus.REVISION_REQUESTED

    db.commit()
    db.refresh(offer_version)

    return offer_version


def create_new_version(db: Session, offer_id: UUID, current_user: User) -> OfferVersion | None:
    offer = get_offer_by_id(db, offer_id)

    if offer is None:
        return None
    request = get_request_by_id(db, offer.request_id)

    if request is None:
        return None
    is_assigned = request.assigned_to_user_id == current_user.id

    if not has_sales_management_access(current_user) and not is_assigned:
        return None

    statement = select(OfferVersion).where(OfferVersion.offer_id == offer_id,
                                           OfferVersion.version_number == offer.current_version)
    current_version = (db.execute(statement).scalar_one_or_none())
    if current_version is None:
        return None

    if current_version.status not in [OfferStatus.REVISION_REQUESTED, OfferStatus.CLIENT_APPROVED]:
        return None

    new_version_number = offer.current_version + 1

    new_version = OfferVersion(
        offer_id=offer.id,
        version_number=new_version_number,
        status=OfferStatus.DRAFT,
        total_price=current_version.total_price,
        total_price_letters=current_version.total_price_letters,
        payment_terms=current_version.payment_terms,
        delivery_terms=current_version.delivery_terms,
        delivery_period=current_version.delivery_period,
        validity_date=current_version.validity_date,
        country_of_origin=current_version.country_of_origin,
        notes=current_version.notes,
    )
    db.add(new_version)
    db.flush()

    copy_document_items(db,
        source_type=DocumentType.OFFER_VERSION,
        source_id=current_version.id,
        target_type=DocumentType.OFFER_VERSION,
        target_id=new_version.id,
    )
    offer.current_version = new_version_number

    db.commit()
    db.refresh(new_version)

    return new_version