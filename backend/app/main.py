from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.user import router as user_router
from app.api.v1.role import router as role_router
from app.api.v1.auth import router as auth_router


app = FastAPI(
    title="Commerce-Flow ERP",
    version="1.0.0",
)

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