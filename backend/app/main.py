from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.user import router as user_router
from app.api.v1.role import router as role_router
from app.api.v1.auth import router as auth_router
from app.api.v1.client import router as client_router
from app.api.v1.supplier import router as supplier_router
from app.api.v1.contact import router as contact_router
from app.api.v1.request import router as request_router
from app.api.v1.item import router as item_router
from app.api.v1.rfq import router as rfq_router
from app.api.v1.quotation import router as quotation_router
from app.api.v1.offer import router as offer_router


app = FastAPI(
    title="Commerce-Flow ERP",
    version="1.0.0",
)

# noinspection PyTypeChecker
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/")
async def health():
    return {"hello": "world"}

app.include_router(user_router)
app.include_router(role_router)
app.include_router(auth_router)

app.include_router(client_router)
app.include_router(supplier_router)
app.include_router(contact_router)

app.include_router(request_router)
app.include_router(item_router)

app.include_router(rfq_router)
app.include_router(quotation_router)

app.include_router(offer_router)