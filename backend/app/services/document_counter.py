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
            "zangabil": f"PO{year_2d}-{number}",
            "awatad": f"PO{year_2d}S{number}",
            "al_araba": f"PO{year_4d}-{number}",
            "al_kowa": f"PO{number}",
        }

    elif document_type == "request":
        formats = {
            "zangabil": f"REQ{year_2d}-{number}",
            "awatad": f"REQ{year_2d}S{number}",
            "al_araba": f"REQ{year_4d}-{number}",
            "al_kowa": f"REQ{number}",
        }

    elif document_type == "rfq":
        formats = {
            "zangabil": f"RFQ{year_2d}-{number}",
            "awatad": f"RFQ{year_2d}S{number}",
            "al_araba": f"RFQ{year_4d}-{number}",
            "al_kowa": f"RFQ{number}",
        }

    elif document_type == "quotation":
        formats = {
            "zangabil": f"QTN{year_2d}-{number}",
            "awatad": f"QTN{year_2d}S{number}",
            "al_araba": f"QTN{year_4d}-{number}",
            "al_kowa": f"QTN{number}",
        }

    elif document_type == "offer":
        formats = {
            "zangabil": f"OFF{year_2d}-{number}",
            "awatad": f"OFF{year_2d}S{number}",
            "al_araba": f"OFF{year_4d}-{number}",
            "al_kowa": f"OFF{number}",
        }

    else:
        formats = {}

    return formats.get(
        company_code,
        f"{document_type.upper()}-{year_4d}-{number}",
    )