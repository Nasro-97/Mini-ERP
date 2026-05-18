from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, required_roles
from app.models import User, DocumentType, OfferStatus
from app.schemas import DocumentItemCreate, DocumentItemUpdate, DocumentItemOut
from app.services import document_item as document_item_service
from app.services import offer as offer_service

router = APIRouter(prefix="/offer-versions", tags=["Offer Version Items"])

EDITABLE_STATUSES = [OfferStatus.DRAFT, OfferStatus.CHANGES_REQUESTED]




@router.get("/{version_id}/items", response_model=list[DocumentItemOut], status_code=status.HTTP_200_OK)
def get_offer_version_items(
    version_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    version = offer_service.get_offer_version_by_id(db, version_id)
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer version not found")

    return document_item_service.get_document_item_by_document(db, DocumentType.OFFER_VERSION, version_id)


@router.post("/{version_id}/items", response_model=DocumentItemOut, status_code=status.HTTP_201_CREATED)
def add_offer_version_item(
    version_id: UUID,
    item_data: DocumentItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(required_roles(["Sales Specialist", "Sales Manager", "COD"]))
):
    version = offer_service.get_offer_version_by_id(db, version_id)
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer version not found")

    if version.status not in EDITABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Items can only be added when version status is DRAFT or CHANGES_REQUESTED"
        )

    return document_item_service.add_document_item(db, DocumentType.OFFER_VERSION, version_id, item_data)


@router.patch("/{version_id}/items/{line_id}", response_model=DocumentItemOut, status_code=status.HTTP_200_OK)
def update_offer_version_item(
    version_id: UUID,
    line_id: UUID,
    item_data: DocumentItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(required_roles(["Sales Specialist", "Sales Manager", "COD"]))
):
    version = offer_service.get_offer_version_by_id(db, version_id)
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer version not found")

    if version.status not in EDITABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Items can only be updated when version status is DRAFT or CHANGES_REQUESTED"
        )

    item = document_item_service.update_document_item(db, line_id, item_data)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    return item


@router.delete("/{version_id}/items/{line_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_offer_version_item(
    version_id: UUID,
    line_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(required_roles(["Sales Specialist", "Sales Manager", "COD"]))
):
    version = offer_service.get_offer_version_by_id(db, version_id)
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer version not found")

    if version.status not in EDITABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Items can only be deleted when version status is DRAFT or CHANGES_REQUESTED"
        )

    deleted = document_item_service.delete_document_item(db, line_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")