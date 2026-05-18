from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models import Item
from app.schemas import ItemCreate, ItemUpdate

def create_item(db: Session,request_id: UUID, item_data: ItemCreate) -> Item:
    existing_count = db.execute(
        select(func.count()).select_from(Item).where(Item.request_id == request_id)
    ).scalar() or 0

    item = Item(
        request_id= request_id,

        line_number= existing_count + 1,
        description=item_data.description,
        quantity=item_data.quantity,
        unit=item_data.unit,

        notes=item_data.notes,
    )

    db.add(item)
    db.commit()

    db.refresh(item)

    return item


def get_item_by_id(db: Session, item_id: UUID) -> Item | None:
    statement = select(Item).where(Item.id == item_id)

    return db.execute(statement).scalar_one_or_none()


def get_items_by_request(db: Session, request_id: UUID) -> list[Item]:
    statement = select(Item).where(Item.request_id == request_id)

    return list(db.execute(statement).scalars().all())


def update_item(db: Session, item_id: UUID, item_data: ItemUpdate) -> Item | None:
    item = get_item_by_id(db, item_id)
    if not item:
        return None

    updated_data = item_data.model_dump(exclude_unset=True)

    for field, value in updated_data.items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)

    return item

def delete_item(db: Session, item_id: UUID) -> bool:
    item = get_item_by_id(db, item_id)

    if item is None:
        return False

    db.delete(item)
    db.commit()

    return True