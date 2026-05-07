from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Contact, Client, Supplier, CompanyType
from app.schemas import ContactCreate, ContactUpdate


# Create contact
def create_contact(db: Session, contact_data: ContactCreate) -> Contact:
    if contact_data.company_type == CompanyType.CLIENT:
        company = db.execute(select(Client).where(Client.id == contact_data.company_id)).scalar_one_or_none()

        if company is None:
            raise ValueError("Client not found")

    elif contact_data.company_type == CompanyType.SUPPLIER:
        company = db.execute(select(Supplier).where(Supplier.id == contact_data.company_id)).scalar_one_or_none()

        if company is None:
            raise ValueError("Supplier not found")

    # Create the contact after validation
    contact = Contact(
        company_type=contact_data.company_type,
        company_id=contact_data.company_id,
        fullname=contact_data.fullname,
        position=contact_data.position,
        email=contact_data.email,
        phone_1=contact_data.phone_1,
        phone_2=contact_data.phone_2,
        is_active=True,
    )

    db.add(contact)
    db.commit()
    db.refresh(contact)

    return contact


def get_contact_by_id(db: Session, contact_id: UUID) -> Contact | None:
    statement = select(Contact).where(Contact.id == contact_id)
    return db.execute(statement).scalar_one_or_none()


# Get all contacts
def get_contacts(db: Session) -> list[Contact]:
    statement = select(Contact)
    return list(db.execute(statement).scalars().all())


# get contact by company name
def get_contacts_by_company( db: Session, company_type: CompanyType, company_id: UUID,) -> list[Contact]:

    statement = select(Contact).where(Contact.company_type == company_type, Contact.company_id == company_id,)

    return list(db.execute(statement).scalars().all())


#update_contact
def update_contact( db: Session, contact_id: UUID, contact_data: ContactUpdate) -> Contact | None:
    contact = get_contact_by_id(db, contact_id)

    if contact is None:
        return None

    update_data = contact_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(contact, field, value)

    db.commit()
    db.refresh(contact)

    return contact

# Deactivate_contact
def deactivate_contact(db: Session, contact_id: UUID) -> Contact | None:
    contact = get_contact_by_id(db, contact_id)

    if contact is None:
        return None

    contact.is_active = False

    db.commit()
    db.refresh(contact)

    return contact


 # Activate contact
def activate_contact(db: Session, contact_id: UUID) -> Contact | None:
    contact = get_contact_by_id(db, contact_id)

    if contact is None:
        return None

    contact.is_active = True

    db.commit()
    db.refresh(contact)

    return contact