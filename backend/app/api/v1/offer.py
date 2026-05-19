from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, required_roles
from app.models import User, DocumentType, OfferStatus
from app.schemas import DocumentItemCreate, DocumentItemUpdate, DocumentItemOut
from app.services import document_item as document_item_service
from app.services import offer as offer_service
from app.schemas import ( OfferCreate, OfferOut, OfferWithVersionsOut, OfferVersionUpdate, OfferVersionOut, CodResponseSchema, ClientResponseSchema)


EDITABLE_STATUSES = [OfferStatus.DRAFT, OfferStatus.CHANGES_REQUESTED]


router = APIRouter(prefix="/offers", tags=["Offers"])


# Offer routes

@router.post("/", response_model=OfferOut, status_code=status.HTTP_201_CREATED)
def create_offer( offer_data: OfferCreate, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["Sales Specialist", "Sales Manager", "COD"]))):
    offer = offer_service.create_offer(db, offer_data, current_user)
    if offer is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create offer. Check request is in OFFER_IN_PROGRESS status, no offer exists yet, and you have permission."
        )
    return offer


@router.get("/request/{request_id}", response_model=OfferWithVersionsOut, status_code=status.HTTP_200_OK)
def get_offer_by_request( request_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    offer = offer_service.get_offer_by_request(db, request_id)
    if offer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No offer found for this request")
    return offer


@router.get("/{offer_id}", response_model=OfferWithVersionsOut, status_code=status.HTTP_200_OK)
def get_offer( offer_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    offer = offer_service.get_offer_with_versions(db, offer_id)
    if offer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")
    return offer


# Offer version routes

@router.patch("/versions/{version_id}", response_model=OfferVersionOut, status_code=status.HTTP_200_OK)
def update_offer_version( version_id: UUID, version_data: OfferVersionUpdate, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["Sales Specialist", "Sales Manager", "COD"]))):
    version = offer_service.update_offer_version(db, version_id, version_data)
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not update version. Check status is DRAFT or CHANGES_REQUESTED."
        )
    return version


@router.patch("/versions/{version_id}/submit", response_model=OfferVersionOut, status_code=status.HTTP_200_OK)
def submit_for_cod_approval( version_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["Sales Specialist", "Sales Manager", "COD"])) ):
    version = offer_service.submit_for_cod_approval(db, version_id, current_user)
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not submit for COD approval. Check status is DRAFT or CHANGES_REQUESTED and you have permission."
        )
    return version


@router.patch("/versions/{version_id}/cod-response", response_model=OfferVersionOut, status_code=status.HTTP_200_OK)
def record_cod_response( version_id: UUID, cod_response: CodResponseSchema, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["COD"]))):
    version = offer_service.record_cod_response(db, version_id, cod_response, current_user)
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not record COD response. Check status is PENDING_COD_APPROVAL and you are COD."
        )
    return version


@router.patch("/versions/{version_id}/send", response_model=OfferVersionOut, status_code=status.HTTP_200_OK)
def send_to_client( version_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["Sales Specialist", "Sales Manager", "COD"]))):
    version = offer_service.send_to_client(db, version_id, current_user)
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not send to client. Check status is COD_APPROVED and you have permission."
        )
    return version


@router.patch("/versions/{version_id}/client-response", response_model=OfferVersionOut, status_code=status.HTTP_200_OK)
def record_client_response( version_id: UUID, client_response: ClientResponseSchema, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["Sales Specialist", "Sales Manager", "COD"]))):
    version = offer_service.record_client_response(db, version_id, client_response, current_user)
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not record client response. Check status is SENT_TO_CLIENT and you have permission."
        )
    return version


@router.post("/{offer_id}/new-version", response_model=OfferVersionOut, status_code=status.HTTP_201_CREATED)
def create_new_version( offer_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["Sales Specialist", "Sales Manager", "COD"]))):
    version = offer_service.create_new_version(db, offer_id, current_user)
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create new version. Check current version is CLIENT_APPROVED or REVISION_REQUESTED and you have permission."
        )
    return version


# Offer Item routes
@router.get("/versions/{version_id}/items", response_model=list[DocumentItemOut], status_code=status.HTTP_200_OK)
def get_offer_version_items( version_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    version = offer_service.get_offer_version_by_id(db, version_id)
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer version not found")
    return document_item_service.get_document_item_by_document(db, DocumentType.OFFER_VERSION, version_id)


@router.post("/versions/{version_id}/items", response_model=DocumentItemOut, status_code=status.HTTP_201_CREATED)
def add_offer_version_item( version_id: UUID, item_data: DocumentItemCreate, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["Sales Specialist", "Sales Manager", "COD"]))):
    version = offer_service.get_offer_version_by_id(db, version_id)
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer version not found")
    if version.status not in EDITABLE_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Version is not editable")
    return document_item_service.add_document_item(db, DocumentType.OFFER_VERSION, version_id, item_data)


@router.patch("/versions/{version_id}/items/{line_id}", response_model=DocumentItemOut, status_code=status.HTTP_200_OK)
def update_offer_version_item( version_id: UUID, line_id: UUID, item_data: DocumentItemUpdate, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["Sales Specialist", "Sales Manager", "COD"]))):
    version = offer_service.get_offer_version_by_id(db, version_id)
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer version not found")
    if version.status not in EDITABLE_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Version is not editable")
    item = document_item_service.update_document_item(db, line_id, item_data)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


@router.delete("/versions/{version_id}/items/{line_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_offer_version_item( version_id: UUID, line_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["Sales Specialist", "Sales Manager", "COD"]))):
    version = offer_service.get_offer_version_by_id(db, version_id)
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer version not found")
    if version.status not in EDITABLE_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Version is not editable")
    deleted = document_item_service.delete_document_item(db, line_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")