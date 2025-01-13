from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext

router = APIRouter()

# Simulace přístupu k databázi (nahradit reálnou implementací)
MOCK_CUSTOMERS = {
    "example_user": {
        "password_hash": "$2b$12$EIXnZaV5l0TnRIRhTbuvSOb7DT4OQl.d6liICZGpG2daLaJGV4Us2",  # bcrypt hash hesla "example_password"
        "customer_id": 1,
        "company": "Example Corp",
        "monthly_tokens": 100,
        "remaining_tokens": 50,
        "visible": 1,
    }
}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    customer_id: int
    name: str
    company: str
    monthly_tokens: int
    remaining_tokens: int


@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest):
    user = MOCK_CUSTOMERS.get(data.username)
    if not user or not user["visible"]:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    if not pwd_context.verify(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid password")

    return {
        "customer_id": user["customer_id"],
        "name": data.username,
        "company": user["company"],
        "monthly_tokens": user["monthly_tokens"],
        "remaining_tokens": user["remaining_tokens"],
    }
