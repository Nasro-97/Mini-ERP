from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Supplier
from app.schemas import SupplierCreate, SupplierUpdate


#Create Supplier
def create_supplier(db: Session, supplier_data: SupplierCreate) -> Supplier:

    supplier = Supplier(
        company_name=supplier_data.company_name,
        email=supplier_data.email,
        phone_1=supplier_data.phone_1,
        phone_2=supplier_data.phone_2,
        address=supplier_data.address,
        is_active=True,
    )

    db.add(supplier)
    db.commit()

    db.refresh(supplier)

    return supplier


# Get supplier by id
def get_supplier_by_id(db: Session, supplier_id: UUID) -> Supplier | None:
    statement = select(Supplier).where(Supplier.id == supplier_id)

    return db.execute(statement).scalar_one_or_none()


# Get supplier by name
def get_supplier_by_name(db: Session, company_name: str) -> Supplier | None:
    statement = select(Supplier).where(Supplier.company_name == company_name)

    return db.execute(statement).scalar_one_or_none()


# Get supplier
def get_suppliers(db: Session) -> list[Supplier]:
    statement = select(Supplier)

    return list( db.execute(statement).scalars().all())


# Update supplier
def update_supplier(db: Session, supplier_data: SupplierUpdate, supplier_id: UUID) -> Supplier | None:
    supplier = get_supplier_by_id(db, supplier_id)

    if supplier is None: return None

    updated_data = supplier_data.model_dump(exclude_unset=True)

    for field, value in updated_data.items():
        setattr(supplier, field, value)

    db.commit()
    db.refresh(supplier)

    return supplier


# Deactivate supplier
def deactivate_supplier(db: Session, supplier_id: UUID) -> Supplier | None:
    supplier = supplier = get_supplier_by_id(db, supplier_id)

    if supplier is None: return None

    supplier.is_active = False

    db.commit()
    db.refresh(supplier)

    return supplier


# Activate supplier
def activate_supplier(db: Session, supplier_id: UUID) -> Supplier | None:
    supplier = supplier = get_supplier_by_id(db, supplier_id)

    if supplier is None: return None

    supplier.is_active = True

    db.commit()
    db.refresh(supplier)

    return supplier
