from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, required_roles
from app.models import User
from app.schemas import QuotationCreate, QuotationOutput
from app.services import quotation as quotation_service
from app.services import rfq as rfq_service

router = APIRouter(prefix="/quotations", tags=["Quotations"])


@router.post("/", response_model=QuotationOutput, status_code=status.HTTP_201_CREATED)
def create_quotation( quotation_data: QuotationCreate, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["Procurement Manager", "Procurement Specialist", "COD"]))):
    quotation = quotation_service.create_quotation(db, quotation_data, current_user)
    if quotation is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create quotation. Check RFQ exists and you have permission."
        )
    return quotation


@router.get("/{quotation_id}", response_model=QuotationOutput, status_code=status.HTTP_200_OK)
def get_quotation_by_id( quotation_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    quotation = quotation_service.get_quotation_by_id(db, quotation_id)
    if quotation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quotation not found"
        )
    return quotation


@router.get("/rfq/{rfq_id}", response_model=list[QuotationOutput], status_code=status.HTTP_200_OK)
def get_quotations_by_rfq( rfq_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rfq = rfq_service.get_rfq_by_id(db, rfq_id)
    if rfq is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RFQ not found"
        )
    return quotation_service.get_quotations_by_rfq(db, rfq_id)


@router.patch("/{quotation_id}/submit", response_model=QuotationOutput, status_code=status.HTTP_200_OK)
def submit_for_review(
    quotation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(required_roles(["Procurement Manager", "Procurement Specialist", "COD"]))
):
    quotation = quotation_service.submit_for_review(db, quotation_id, current_user)
    if quotation is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not submit quotation. Check status is RECEIVED and you have permission."
        )
    return quotation


@router.patch("/{quotation_id}/approve", response_model=QuotationOutput, status_code=status.HTTP_200_OK)
def approve_quotation(
    quotation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(required_roles(["Procurement Manager", "COD"]))
):
    quotation = quotation_service.approve_quotation(db, quotation_id, current_user)
    if quotation is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not approve quotation. Check status is UNDER_REVIEW and you have permission."
        )
    return quotation


@router.patch("/{quotation_id}/reject", response_model=QuotationOutput, status_code=status.HTTP_200_OK)
def reject_quotation(
    quotation_id: UUID,
    rejection_notes: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(required_roles(["Procurement Manager", "COD"]))
):
    quotation = quotation_service.reject_quotation(db, quotation_id, rejection_notes, current_user)
    if quotation is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not reject quotation. Check status is UNDER_REVIEW and you have permission."
        )
    return quotation


@router.patch("/{quotation_id}/reopen", response_model=QuotationOutput, status_code=status.HTTP_200_OK)
def reopen_quotation(
    quotation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(required_roles(["Procurement Manager", "Procurement Specialist", "COD"]))
):
    quotation = quotation_service.reopen_quotation(db, quotation_id, current_user)
    if quotation is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not reopen quotation. Check status is REJECTED and you have permission."
        )
    return quotation