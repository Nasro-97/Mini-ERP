from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, required_roles
from app.models import User, POStatus, DocumentType
from app.schemas import PurchaseOrderCreate, PurchaseOrderUpdate, PurchaseOrderOutput, DocumentItemCreate, DocumentItemUpdate, DocumentItemOut
from app.services import purchase_order as po_service
from app.services import document_item as document_item_service


router = APIRouter(prefix="/purchase-orders", tags=["Purchase Orders"])


@router.post("/", response_model=PurchaseOrderOutput, status_code=status.HTTP_201_CREATED)
def create_purchase_order( po_data: PurchaseOrderCreate, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["COD", "Procurement Manager", "Procurement Specialist"])),):
    purchase_order = po_service.create_po(db, po_data, current_user)

    if purchase_order is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Purchase order could not be created",
        )

    return purchase_order


@router.get("/request/{request_id}", response_model=PurchaseOrderOutput, status_code=status.HTTP_200_OK)
def get_purchase_order_by_request( request_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    purchase_order = po_service.get_po_by_request(db, request_id)

    if purchase_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found for this request",
        )

    return purchase_order


@router.patch("/{po_id}/send", response_model=PurchaseOrderOutput, status_code=status.HTTP_200_OK)
def send_purchase_order(po_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["COD", "Procurement Manager", "Procurement Specialist"]))):
    purchase_order = po_service.send_po(db, po_id, current_user)

    if purchase_order is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Purchase order not found, not in draft status, or you do not have permission",
        )

    return purchase_order


@router.patch("/{po_id}/accept", response_model=PurchaseOrderOutput, status_code=status.HTTP_200_OK)
def accept_purchase_order(po_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["COD", "Procurement Manager", "Procurement Specialist"]))):
    purchase_order = po_service.accept_po(db, po_id, current_user)

    if purchase_order is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Purchase order not found, not sent, or you do not have permission",
        )

    return purchase_order


@router.get("/{po_id}", response_model=PurchaseOrderOutput, status_code=status.HTTP_200_OK)
def get_purchase_order_by_id( po_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    purchase_order = po_service.get_po_by_id(db, po_id)

    if purchase_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )

    return purchase_order


@router.patch("/{po_id}", response_model=PurchaseOrderOutput, status_code=status.HTTP_200_OK)
def update_purchase_order( po_id: UUID, po_data: PurchaseOrderUpdate, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["COD", "Procurement Manager", "Procurement Specialist"]))):
    purchase_order = po_service.update_po(db, po_id, po_data, current_user)

    if purchase_order is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Purchase order not found, not editable, or you do not have permission",
        )

    return purchase_order



@router.delete("/{po_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_purchase_order(po_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["COD", "Procurement Manager", "Procurement Specialist"]))):
    deleted = po_service.delete_po(db, po_id, current_user)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Purchase order not found, not draft, or you do not have permission",
        )


@router.get("/{po_id}/items", response_model=list[DocumentItemOut], status_code=status.HTTP_200_OK)
def get_purchase_order_items(po_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    purchase_order = po_service.get_po_by_id(db, po_id)

    if purchase_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )

    return document_item_service.get_document_item_by_document(db, DocumentType.PURCHASE_ORDER, po_id)


@router.post("/{po_id}/items", response_model=DocumentItemOut, status_code=status.HTTP_201_CREATED)
def add_purchase_order_item(po_id: UUID, item_data: DocumentItemCreate, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["COD", "Procurement Manager", "Procurement Specialist"]))):
    purchase_order = po_service.get_po_by_id(db, po_id)

    if purchase_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )

    if purchase_order.status != POStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Items can only be added when purchase order status is DRAFT",
        )

    return document_item_service.add_document_item(db, DocumentType.PURCHASE_ORDER, po_id, item_data)


@router.patch("/{po_id}/items/{line_id}", response_model=DocumentItemOut, status_code=status.HTTP_200_OK)
def update_purchase_order_item(po_id: UUID, line_id: UUID, item_data: DocumentItemUpdate, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["COD", "Procurement Manager", "Procurement Specialist"]))):
    purchase_order = po_service.get_po_by_id(db, po_id)

    if purchase_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )

    if purchase_order.status != POStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Items can only be updated when purchase order status is DRAFT",
        )

    item = document_item_service.update_document_item(db, line_id, item_data)

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    return item


@router.patch("/{po_id}/request-changes", response_model=PurchaseOrderOutput)
def request_po_changes(po_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    purchase_order = po_service.request_po_changes(db, po_id, current_user)

    if purchase_order is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot request changes for this purchase order.",
        )

    return purchase_order


@router.delete("/{po_id}/items/{line_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_purchase_order_item(po_id: UUID, line_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["COD", "Procurement Manager", "Procurement Specialist"]))):
    purchase_order = po_service.get_po_by_id(db, po_id)

    if purchase_order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )

    if purchase_order.status != POStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Items can only be deleted when purchase order status is DRAFT",
        )

    deleted = document_item_service.delete_document_item(db, line_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )