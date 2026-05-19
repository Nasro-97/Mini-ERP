from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DocumentItem, DocumentType
from app.schemas import DocumentItemCreate, DocumentItemUpdate


def get_document_item_by_id( db: Session, item_id: UUID) -> DocumentItem| None:
    statement =select(DocumentItem).where(DocumentItem.id == item_id)
    return db.execute(statement).scalar_one_or_none()


def get_document_item_by_document(db: Session, document_type: DocumentType, document_id: UUID) -> list[DocumentItem]:
    statement = select(DocumentItem).where(DocumentItem.document_type == document_type,
                                           DocumentItem.document_id == document_id
    ).order_by(DocumentItem.line_number)
    return list(db.execute(statement).scalars().all())


def add_document_item(db: Session,document_type: DocumentType,document_id: UUID ,item_data: DocumentItemCreate) -> DocumentItem:
    item = DocumentItem(
        item_id=item_data.item_id,
        document_type=document_type,
        document_id=document_id,

        line_number=item_data.line_number,
        description=item_data.description,
        quantity=item_data.quantity,
        unit=item_data.unit,

        origin_country=item_data.origin_country,
        warranty=item_data.warranty,
        unit_price=item_data.unit_price,
        total_price=item_data.total_price,
        currency=item_data.currency,

        hs_code=item_data.hs_code,
        package_count=item_data.package_count,
        gross_weight_kg=item_data.gross_weight_kg,
        net_weight_kg=item_data.net_weight_kg,
        dimensions_cm=item_data.dimensions_cm,

        extra_data=item_data.extra_data,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return item


def update_document_item(db: Session, item_id: UUID, item_data: DocumentItemUpdate) -> DocumentItem | None:
    item= get_document_item_by_id(db, item_id)
    if item is None: return None

    update_data = item_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)

    return item


def copy_document_items(db: Session, source_type: DocumentType, source_id: UUID, target_type: DocumentType, target_id: UUID) -> list[DocumentItem]:
    source_items = get_document_item_by_document(db, source_type, source_id)
    new_items = []

    for item in source_items:
        new_item = DocumentItem(
            item_id= item.item_id,
            document_type= target_type,
            document_id= target_id,
            line_number= item.line_number,
            description= item.description,
            quantity= item.quantity,
            unit= item.unit,
            origin_country= item.origin_country,
            warranty= item.warranty,
            unit_price= item.unit_price,
            total_price= item.total_price,
            currency= item.currency,
            hs_code= item.hs_code,
            package_count= item.package_count,
            gross_weight_kg= item.gross_weight_kg,
            net_weight_kg= item.net_weight_kg,
            dimensions_cm= item.dimensions_cm,
            extra_data= item.extra_data,
        )
        db.add(new_item)
        new_items.append(new_item)

    db.flush()
    return new_items


def copy_items_from_request(db: Session, request_id: UUID, version_id: UUID) -> None:
    from app.models import Item

    items = db.execute(select(Item).where(Item.request_id == request_id).order_by(Item.line_number)).scalars().all()

    for item in items:
        line = DocumentItem(
            item_id=item.id,
            document_type=DocumentType.OFFER_VERSION,
            document_id=version_id,
            line_number=item.line_number,
            description=item.description,
            quantity=item.quantity,
            unit=item.unit,
        )
        db.add(line)

    db.flush()


def delete_document_item(db: Session, item_id: UUID) -> bool:
    item = get_document_item_by_id(db, item_id)

    if item is None:
        return False

    db.delete(item)
    db.commit()

    return True

