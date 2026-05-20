from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, required_roles
from app.schemas import ItemUpdate, ItemOutput
from app.services import item as item_service
from app.services import request as request_service
from app.models import User, RequestStatus

router = APIRouter(prefix="/items", tags=["Items"])


# Get one item by id
# noinspection PyUnusedLocal
@router.get("/{item_id}", response_model=ItemOutput, status_code=status.HTTP_200_OK)
def get_item_by_id( item_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = item_service.get_item_by_id(db, item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return item


@router.patch("/{item_id}", response_model=ItemOutput, status_code=status.HTTP_200_OK)
def update_item(item_id: UUID, item_data: ItemUpdate, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["Sales Specialist", "Sales Manager", "COD"]))):
    item = item_service.get_item_by_id(db, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    request = request_service.get_request_by_id(db, item.request_id)
    if request is None or request.status != RequestStatus.DRAFT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Items can only be modified when request is in draft status")

    updated = item_service.update_item(db, item_id, item_data)
    return updated


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["Sales Specialist", "Sales Manager", "COD"]))):
    item = item_service.get_item_by_id(db, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    request = request_service.get_request_by_id(db, item.request_id)
    if request is None or request.status != RequestStatus.DRAFT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Items can only be deleted when request is in draft status")

    item_service.delete_item(db, item_id)