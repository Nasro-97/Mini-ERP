from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user

from app.models import User, Quotation, Supplier, PurchaseOrder, Request, DocumentType

from app.services.settings import get_settings
from app.services.pdf_generator import render_template, html_to_pdf
from app.services.document_item import get_document_item_by_document
from app.services.offer import get_offer_with_versions


router = APIRouter(prefix="/pdf", tags=["PDF"])


@router.get("/offers/{offer_id}/{pdf_type}")
def generate_offer_pdf(offer_id: UUID, pdf_type: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if pdf_type not in ["technical", "commercial"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="pdf_type must be 'technical' or 'commercial'",
        )

    offer = get_offer_with_versions(db, offer_id)

    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Offer not found",
        )

    request = db.get(Request, offer.request_id) if offer.request_id else None
    quotation = db.get(Quotation, offer.quotation_id) if offer.quotation_id else None

    supplier = None
    if quotation and quotation.supplier_id:
        supplier = db.get(Supplier, quotation.supplier_id)

    current_version = None
    for version in offer.versions:
        if version.version_number == offer.current_version:
            current_version = version
            break

    items = []
    if current_version:
        items = get_document_item_by_document(
            db=db,
            document_type=DocumentType.OFFER_VERSION,
            document_id=current_version.id,
        )

    settings = get_settings(db)
    company_logo_url = (
        f"http://127.0.0.1:8000{settings.company_logo_url}"
        if settings.company_logo_url
        else None
    )

    if pdf_type == "technical":
        html_template = settings.technical_offer_template
        document_title = "Technical Offer"
        show_prices = False
    else:
        html_template = settings.commercial_offer_template
        document_title = "Commercial Offer"
        show_prices = True

    context = {
        "document": {
            "title": document_title,
            "type": pdf_type,
        },
        "company": {
            "email": settings.company_email,
            "phone": settings.company_phone,
            "logo_url": company_logo_url,
        },
        "offer": offer,
        "offer_version": current_version,
        "request": request,
        "quotation": quotation,
        "supplier": supplier,
        "items": items,
        "show_prices": show_prices,
    }

    html = render_template(html_template, context)
    pdf_bytes = html_to_pdf(html)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{pdf_type}-offer-{offer.offer_number}.pdf"'
        },
    )

@router.get("/purchase-orders/{po_id}")
def generate_purchase_order_pdf( po_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    po = db.get(PurchaseOrder, po_id)

    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase order not found",
        )

    request = db.get(Request, po.request_id) if po.request_id else None
    quotation = db.get(Quotation, po.quotation_id) if po.quotation_id else None
    supplier = db.get(Supplier, po.supplier_id) if po.supplier_id else None

    items = get_document_item_by_document(
        db=db,
        document_type=DocumentType.PURCHASE_ORDER,
        document_id=po.id,
    )

    settings = get_settings(db)
    company_logo_url = (
        f"http://127.0.0.1:8000{settings.company_logo_url}"
        if settings.company_logo_url
        else None
    )

    context = {
        "document": {
            "title": "Purchase Order",
            "type": "purchase_order",
        },
        "company": {
            "email": settings.company_email,
            "phone": settings.company_phone,
            "logo_url": company_logo_url,
        },
        "po": po,
        "request": request,
        "quotation": quotation,
        "supplier": supplier,
        "items": items,
        "show_prices": True,
    }

    html = render_template(settings.po_template, context)
    pdf_bytes = html_to_pdf(html)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="purchase-order-{po.po_number}.pdf"'
        },
    )