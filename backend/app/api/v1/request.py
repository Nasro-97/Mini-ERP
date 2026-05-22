from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, required_roles
from app.schemas.request import RequestCreate, RequestUpdate, RequestOutput, RequestWithItems
from app.schemas.item import ItemCreate, ItemOutput
from app.services import request as request_service
from app.services import item as item_service
from app.models import User, RequestStatus

router = APIRouter(prefix="/requests", tags=["Requests"])


# Create request + items in one call
@router.post("/", response_model=RequestWithItems, status_code=status.HTTP_201_CREATED)
def create_request( request_data: RequestCreate, items: list[ItemCreate] = Body(default=[]), db: Session = Depends(get_db), current_user: User = Depends(required_roles(["Sales Specialist", "Sales Manager","COD"]))):
    new_request = request_service.create_request(db, request_data, current_user)

    for item_data in items:
        item_service.create_item(db, new_request.id, item_data)

    return request_service.get_request_with_items(db, new_request.id)


# Get all requests — filtered by role automatically
@router.get("/", response_model=list[RequestOutput], status_code=status.HTTP_200_OK)
def get_requests( status_filter: RequestStatus | None = None, client_id: UUID | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return request_service.get_requests(db, current_user)


# Get one request with its items
@router.get("/{request_id}", response_model=RequestWithItems, status_code=status.HTTP_200_OK)
def get_request_by_id( request_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    request = request_service.get_request_with_items(db, request_id)

    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
    return request


# Update request general fields
@router.patch("/{request_id}", response_model=RequestOutput, status_code=status.HTTP_200_OK)
def update_request( request_id: UUID, request_data: RequestUpdate, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["Sales Specialist", "Sales Manager","COD"]))):
    request = request_service.update_request(db, request_id, request_data)

    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
    return request


# Submit for sales manager review
@router.patch("/{request_id}/submit", response_model=RequestOutput, status_code=status.HTTP_200_OK)
def submit_for_review( request_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["Sales Specialist", "COD","Sales Manager"]))):
    request = request_service.submit_for_review(db, request_id)
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request not found or not in DRAFT status"
        )
    return request


# Approve request
@router.patch("/{request_id}/approve", response_model=RequestOutput, status_code=status.HTTP_200_OK)
def approve_request( request_id: UUID, notes: str | None = None, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["Sales Manager", "COD"]))):
    request = request_service.approve_request(db, request_id, current_user, notes)
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request not found or not in PENDING_SALES_MANAGER_APPROVAL status"
        )
    return request


# Reject request
@router.patch("/{request_id}/reject", response_model=RequestOutput, status_code=status.HTTP_200_OK)
def reject_request( request_id: UUID, notes: str, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["Sales Manager", "COD"]))):
    request = request_service.reject_request(db, request_id, current_user, notes)
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request not found or not in PENDING_SALES_MANAGER_APPROVAL status"
        )
    return request


@router.patch("/{request_id}/assign-procurement", response_model=RequestOutput, status_code=status.HTTP_200_OK)
def assign_procurement(request_id: UUID, assigned_user_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["Procurement Manager","COD", "Sales Manager"]))):
    request = request_service.assign_procurement(db, request_id, assigned_user_id, current_user)

    if request is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request not found, not in APPROVED_FOR_SOURCING status, or assigned user does not have a procurement role"
        )

    return request


# Delete request — only if DRAFT
@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_request( request_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["COD","Sales Specialist", "Sales Manager"]))):
    deleted = request_service.delete_request(db, request_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request not found or cannot be deleted after submission"
        )


# Get items for a request
@router.get("/{request_id}/items", response_model=list[ItemOutput], status_code=status.HTTP_200_OK)
def get_items_by_request( request_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    request = request_service.get_request_by_id(db, request_id)
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
    return item_service.get_items_by_request(db, request_id)


# Add item to existing request
@router.post("/{request_id}/items", response_model=ItemOutput, status_code=status.HTTP_201_CREATED)
def create_item( request_id: UUID, item_data: ItemCreate, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["COD","Sales Specialist", "Sales Manager"]))):
    request = request_service.get_request_by_id(db, request_id)
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
    if request.status != RequestStatus.DRAFT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Items can only be added when request is in draft status")

    return item_service.create_item(db, request_id, item_data)

