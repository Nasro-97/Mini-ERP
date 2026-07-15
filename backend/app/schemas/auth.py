from pydantic import BaseModel, EmailStr

# What the frontend sends when the user logs in
class LoginRequest(BaseModel):
    company_code: str
    email: EmailStr
    password: str

# What the backend returns after successful login
class TokenResponse(BaseModel):

    access_token: str
    token_type: str = "bearer"