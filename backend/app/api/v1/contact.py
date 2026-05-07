from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import required_roles
from app.models.contact import CompanyType
from app.schemas import ContactCreate, ContactUpdate, ContactOut
from app.services import contact as contact_service


router = APIRouter(prefix="/contacts", tags=["Contacts"])

# Roles allowed to create, update, activate, and deactivate contacts
allowed_roles = ["COD", "Sales Manager", "Procurement Manager"]


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ContactOut)
def create_contact( contact_data: ContactCreate, db: Session = Depends(get_db), current_user=Depends(required_roles(allowed_roles))):
    try:
        return contact_service.create_contact(db, contact_data)

    except ValueError as error:
        # Example: client_id/supplier_id does not exist
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[ContactOut])
def get_contacts(db: Session = Depends(get_db)):
    # Return all contacts
    return contact_service.get_contacts(db)


@router.get("/company/{company_type}/{company_id}", status_code=status.HTTP_200_OK, response_model=list[ContactOut])
def get_contacts_by_company( company_type: CompanyType, company_id: UUID, db: Session = Depends(get_db)):
    return contact_service.get_contacts_by_company(
        db=db,
        company_type=company_type,
        company_id=company_id,
    )


@router.patch("/{contact_id}", status_code=status.HTTP_200_OK, response_model=ContactOut)
def update_contact( contact_id: UUID, contact_data: ContactUpdate, db: Session = Depends(get_db), current_user=Depends(required_roles(allowed_roles))):
    contact = contact_service.update_contact(db, contact_id, contact_data)

    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )

    return contact


@router.patch("/{contact_id}/deactivate", status_code=status.HTTP_200_OK, response_model=ContactOut)
def deactivate_contact( contact_id: UUID, db: Session = Depends(get_db), current_user=Depends(required_roles(allowed_roles))):
    contact = contact_service.deactivate_contact(db, contact_id)

    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )

    return contact


@router.patch("/{contact_id}/activate", status_code=status.HTTP_200_OK, response_model=ContactOut)
def activate_contact( contact_id: UUID, db: Session = Depends(get_db), current_user=Depends(required_roles(allowed_roles))):
    contact = contact_service.activate_contact(db, contact_id)

    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )

    return contact


@router.get("/{contact_id}", status_code=status.HTTP_200_OK, response_model=ContactOut)
def get_contact_by_id( contact_id: UUID, db: Session = Depends(get_db)):
    contact = contact_service.get_contact_by_id(db, contact_id)

    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found",
        )

    return contact