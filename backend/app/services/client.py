from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Client
from app.schemas import ClientCreate, ClientUpdate


#Create Client
def create_client(db: Session, client_data: ClientCreate) -> Client:

    client = Client(
        company_name=client_data.company_name,
        email=client_data.email,
        phone_1=client_data.phone_1,
        phone_2=client_data.phone_2,
        address=client_data.address,
        is_active=True,
    )

    db.add(client)
    db.commit()

    db.refresh(client)

    return client


# Get client by id
def get_client_by_id(db: Session, client_id: UUID) -> Client | None:
    statement = select(Client).where(Client.id == client_id)

    return db.execute(statement).scalar_one_or_none()


# Get client by name
def get_client_by_name(db: Session, company_name: str) -> Client | None:
    statement = select(Client).where(Client.company_name == company_name)

    return db.execute(statement).scalar_one_or_none()


# Get clients
def get_clients(db: Session) -> list[Client]:
    statement = select(Client)

    return list( db.execute(statement).scalars().all())


# Update Client
def update_client(db: Session, client_data: ClientUpdate, client_id: UUID) -> Client | None:
    statement = select(Client).where(Client.id == client_id)
    client = db.execute(statement).scalar_one_or_none()

    if client is None: return None

    updated_data = client_data.model_dump(exclude_unset=True)

    for field, value in updated_data.items():
        setattr(client, field, value)

    db.commit()
    db.refresh(client)

    return client


# Deactivate client
def deactivate_client(db: Session, client_id: UUID) -> Client | None:
    statement = select(Client).where(Client.id == client_id)
    client = db.execute(statement).scalar_one_or_none()

    if client is None: return None

    client.is_active = False

    db.commit()
    db.refresh(client)

    return client


# Activate client
def activate_client(db: Session, client_id: UUID) -> Client | None:
    statement = select(Client).where(Client.id == client_id)
    client = db.execute(statement).scalar_one_or_none()

    if client is None: return None

    client.is_active = True

    db.commit()
    db.refresh(client)

    return client
