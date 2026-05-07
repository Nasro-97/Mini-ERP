from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from app.models import Role
from app.schemas import RoleCreate, RoleUpdate


# Create role
def create_role(db: Session, role: RoleCreate) -> Role:
    role = Role(
        name=role.name,
        description=role.description,
    )

    # Add the role to the database and commit it
    db.add(role)
    db.commit()

    #refresh the database for role so that it gets generated id
    db.refresh(role)

    return role

# get role by id
def get_role_by_id(db: Session, role_id: UUID) -> Role | None:
    statement = select(Role).where(Role.id == role_id)

    return db.execute(statement).scalar_one_or_none()

# get role by name
def get_role_by_name(db: Session, name: str) -> Role | None:
    statement = select(Role).where(Role.name == name)

    return db.execute(statement).scalar_one_or_none()

#list roles
def get_roles(db: Session) -> list[Role]:
    statement = select(Role)

    return list (db.execute(statement).scalars().all())

# update role
def update_role(db: Session, role_id: UUID, role_data: RoleUpdate) -> Role| None:

    statement = select(Role).where(Role.id == role_id)
    role = db.execute(statement).scalar_one_or_none()

    if role is None: return None

    # Update only the fields sent by the backend and conserve the unsent fields
    updated_data = role_data.model_dump(exclude_unset=True)

    for field, value in updated_data.items():
        setattr(role, field, value)

    db.commit()
    db.refresh(role)

    return role

#delete role
def delete_role(db: Session, role_id: UUID) -> None:
    statement = delete(Role).where(Role.id == role_id)
    db.execute(statement)



