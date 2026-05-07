from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.schemas import RoleCreate, RoleUpdate, RoleOut
from app.services import role as role_services
from app.core.dependencies import required_roles

router = APIRouter(prefix="/roles", tags=["Roles"])

# Only COD is allowed to create, delete and update roles


# Create role route
@router.post("/", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
def create_role(role_data: RoleCreate, db: Session = Depends(get_db), current_user = Depends(required_roles(["COD"]))):
    existing_name = role_services.get_role_by_name(db, name=role_data.name)
    if existing_name:
        raise HTTPException(status_code=400, detail="Role already exists")

    return role_services.create_role(db, role_data)


# Get all routes
@router.get("/", response_model=list[RoleOut], status_code=status.HTTP_200_OK)
def get_all_roles(db: Session = Depends(get_db)):
    return role_services.get_roles(db)


# Get role by id
@router.get("/{role_id}", response_model=RoleOut, status_code=status.HTTP_200_OK)
def get_role(role_id: UUID, db: Session = Depends(get_db)):
    role = role_services.get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    return role


# update role
@router.patch("/{role_id}", response_model=RoleOut, status_code=status.HTTP_200_OK)
def update_role(role_id: UUID, role: RoleUpdate, db: Session = Depends(get_db), current_user = Depends(required_roles(["COD"]))):
    existing_role = role_services.get_role_by_id(db, role_id)
    if not existing_role:
        raise HTTPException(status_code=404, detail="Role not found")

    return role_services.update_role(db, role_id, role)


#delete role
@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(role_id: UUID, db: Session = Depends(get_db), current_user = Depends(required_roles(["COD"]))):
    role = role_services.get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    # don't return anything because 204 means NO CONTENT
    role_services.delete_role(db, role_id)
