from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    COMPANY_NAME: str
    COMPANY_EMAIL: str
    COMPANY_PHONE: str
    COMPANY_ADDRESS: str

    RFQ_EMAIL_SUBJECT: str = "Request for Quotation — {request_number}"
    RFQ_EMAIL_GREETING: str = "Dear {to_name},"
    RFQ_EMAIL_INTRO: str = "We kindly request your best quotation for the following items:"
    RFQ_EMAIL_REQUIREMENTS: str = "Please include in your quotation:\n- Unit price and total price\n- Brand, model, and country of origin\n- Warranty terms\n- Lead time\n- Payment terms\n- Validity of quotation"
    RFQ_EMAIL_CLOSING: str = "Regards,"

    class Config:
        env_file = ".env"

settings = Settings()

