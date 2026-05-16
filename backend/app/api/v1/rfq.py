from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, required_roles
from app.models import User
from app.schemas import RFQCreate, RFQUpdate, RFQOutput
from app.services import rfq as rfq_service

router = APIRouter(prefix="/rfqs", tags=["RFQs"])


@router.post("/", response_model=RFQOutput, status_code=status.HTTP_201_CREATED)
def create_rfq( rfq_data: RFQCreate, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["Procurement Manager", "Procurement Specialist", "COD"]))):
    rfq = rfq_service.create_rfq(db, rfq_data, current_user)
    if rfq is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create RFQ. Check request status and permissions."
        )
    return rfq


@router.get("/{rfq_id}", response_model=RFQOutput, status_code=status.HTTP_200_OK)
def get_rfq_by_id( rfq_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rfq = rfq_service.get_rfq_by_id(db, rfq_id)
    if rfq is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RFQ not found"
        )
    return rfq


@router.get("/request/{request_id}", response_model=list[RFQOutput], status_code=status.HTTP_200_OK)
def get_rfqs_by_request( request_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return rfq_service.get_rfqs_by_request(db, request_id)


@router.patch("/{rfq_id}", response_model=RFQOutput, status_code=status.HTTP_200_OK)
def update_rfq( rfq_id: UUID, rfq_data: RFQUpdate, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["Procurement Manager", "Procurement Specialist", "COD"]))):
    rfq = rfq_service.update_rfq(db, rfq_id, rfq_data, current_user)
    if rfq is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not update RFQ. Check status is DRAFT and you have permission."
        )
    return rfq


@router.post("/{rfq_id}/generate-mailto", status_code=status.HTTP_200_OK)
def generate_mailto( rfq_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["Procurement Manager", "Procurement Specialist", "COD"]))):
    result = rfq_service.generate_mailto(db, rfq_id, current_user)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not generate mailto. Check RFQ status is DRAFT and you have permission."
        )
    return result


@router.patch("/{rfq_id}/decline", response_model=RFQOutput, status_code=status.HTTP_200_OK)
def decline_rfq( rfq_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["Procurement Manager", "Procurement Specialist", "COD"]))):
    rfq = rfq_service.decline_rfq(db, rfq_id, current_user)
    if rfq is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not decline RFQ. Check status is SENT and you have permission."
        )
    return rfq


@router.delete("/{rfq_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rfq( rfq_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["Procurement Manager", "Procurement Specialist", "COD"]))):
    deleted = rfq_service.delete_rfq(db, rfq_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not delete RFQ. Only DRAFT RFQs can be deleted."
        )