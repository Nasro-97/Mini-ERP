from datetime import datetime

from sqlalchemy import select

from sqlalchemy.orm import Session

from app.models import DocumentCounter

def generate_document_number(db: Session, document_type: str, company_code: str) -> str:
    current_year = datetime.now().year
    year_2d = str(current_year)[2:]
    year_4d = str(current_year)

    statement = (
        select(DocumentCounter)
        .where(DocumentCounter.document_type == document_type)
        .where(DocumentCounter.company_code == company_code)
        .where(DocumentCounter.year == current_year)
        .with_for_update()
    )

    counter = db.execute(statement).scalar_one_or_none()

    if counter is None:
        counter = DocumentCounter(
            document_type=document_type,
            company_code=company_code,
            year=current_year,
            next_number=1,
        )
        db.add(counter)
        db.flush()

    number = str(counter.next_number).zfill(3)
    counter.next_number += 1

    if document_type == "po":
        formats = {
            "company1": f"PO{year_2d}-{number}",
            "company2": f"PO{year_2d}S{number}",
            "company3": f"PO{year_4d}-{number}",
            "company4": f"PO{number}",
        }
    elif document_type == "request":
        formats = {
            "company1": f"REQ{year_2d}-{number}",
            "company2": f"REQ{year_2d}S{number}",
            "company3": f"REQ{year_4d}-{number}",
            "company4": f"REQ{number}",
        }
    else:
        formats = {}

    return formats.get(company_code, f"{document_type.upper()}-{year_4d}-{number}")