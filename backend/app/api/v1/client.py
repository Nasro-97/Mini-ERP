from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import required_roles
from app.schemas import ClientCreate, ClientUpdate, ClientOut
from app.services import client as client_service

router = APIRouter(prefix="/clients", tags=["Clients"])

# Roles allowed to create, update, activate, and deactivate clients
allowed_roles = ["COD", "Sales Manager", "Sales Specialist"]


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ClientOut)
def create_client(client_data: ClientCreate, db: Session = Depends(get_db), current_user = Depends(required_roles(allowed_roles))):
    existing_client = client_service.get_client_by_name(db, client_data.company_name)

    if existing_client:
        raise HTTPException(status_code=400, detail="Client already exists")

    return client_service.create_client(db, client_data)


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[ClientOut])
def get_clients(db: Session = Depends(get_db)):
    return client_service.get_clients(db)


#deactivate and activate are only possible by the roles : "COD", "Sales Manager", "Sales Specialist"
@router.patch("/{client_id}/deactivate", status_code=status.HTTP_200_OK, response_model=ClientOut)
def deactivate_company(client_id: UUID, db: Session = Depends(get_db), current_user=Depends(required_roles(allowed_roles))):
    client = client_service.deactivate_client(db, client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    return client


# activate and activate are only possible by the roles : "COD", "Sales Manager", "Sales Specialist"
@router.patch("/{client_id}/activate", status_code=status.HTTP_200_OK, response_model=ClientOut)
def activate_company(client_id, db: Session = Depends(get_db), current_user=Depends(required_roles(allowed_roles))):
    client = client_service.activate_client(db, client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    return client


@router.patch("/{client_id}", status_code=status.HTTP_200_OK, response_model=ClientOut)
def update_client(client_id: UUID, client_data: ClientUpdate, db: Session = Depends(get_db),
                  current_user=Depends(required_roles(allowed_roles))):
    client = client_service.update_client(db, client_data, client_id)

    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    return client




@router.get("/{client_id}", status_code=status.HTTP_200_OK, response_model=ClientOut)
def get_company_by_id(client_id: UUID, db: Session = Depends(get_db)):
    client = client_service.get_client_by_id(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client