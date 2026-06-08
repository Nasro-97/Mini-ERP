from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import required_roles
from app.schemas import SupplierCreate, SupplierUpdate, SupplierOut
from app.services import supplier as supplier_service


router = APIRouter(prefix="/suppliers", tags=["Suppliers"])

# Roles allowed to create, update, activate, and deactivate suppliers
allowed_roles = ["COD", "Procurement Specialist", "Procurement Manager"]


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=SupplierOut)
def create_supplier( supplier_data: SupplierCreate, db: Session = Depends(get_db), current_user=Depends(required_roles(allowed_roles)),):

    existing_supplier = supplier_service.get_supplier_by_name(
        db,
        supplier_data.company_name,
    )

    if existing_supplier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Supplier already exists",
        )

    return supplier_service.create_supplier(db, supplier_data)


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[SupplierOut])
def get_suppliers(db: Session = Depends(get_db)):
    # Return all suppliers
    return supplier_service.get_suppliers(db)


@router.patch("/{supplier_id}", status_code=status.HTTP_200_OK, response_model=SupplierOut)
def update_supplier( supplier_id: UUID, supplier_data: SupplierUpdate, db: Session = Depends(get_db), current_user=Depends(required_roles(allowed_roles))):
    supplier = supplier_service.update_supplier(db, supplier_data, supplier_id)

    if supplier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )

    return supplier


@router.patch("/{supplier_id}/deactivate", status_code=status.HTTP_200_OK, response_model=SupplierOut)
def deactivate_supplier( supplier_id: UUID, db: Session = Depends(get_db), current_user=Depends(required_roles(allowed_roles))):
    supplier = supplier_service.deactivate_supplier(db, supplier_id)

    if supplier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )

    return supplier


@router.patch("/{supplier_id}/activate", status_code=status.HTTP_200_OK, response_model=SupplierOut)
def activate_supplier( supplier_id: UUID, db: Session = Depends(get_db), current_user=Depends(required_roles(allowed_roles))):
    supplier = supplier_service.activate_supplier(db, supplier_id)

    if supplier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )

    return supplier


@router.get("/{supplier_id}", status_code=status.HTTP_200_OK, response_model=SupplierOut)
def get_supplier_by_id( supplier_id: UUID, db: Session = Depends(get_db)):
    supplier = supplier_service.get_supplier_by_id(db, supplier_id)

    if supplier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )

    return supplier