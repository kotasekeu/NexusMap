# routes.py
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import mysql.connector

# Konfigurace databáze
DB_CONFIG = {
    "host": "localhost",
    "user": "user",
    "password": "password",
    "database": "db_name"
}

# Inicializace routeru
router = APIRouter()

# OAuth2 konfigurace
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str

@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest):
    # Mock autentizace (nahradit reálnou logikou)
    if data.username != "admin" or data.password != "secret":
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": "mocktoken", "token_type": "bearer"}

class CustomerDetail(BaseModel):
    id: int
    name: str
    company: str
    email: str

@router.get("/customers/{customer_id}", response_model=CustomerDetail)
async def get_customer(customer_id: int, token: str = Depends(oauth2_scheme)):
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT id, name, company, email
        FROM customers
        WHERE id = %s
        """
        cursor.execute(query, (customer_id,))
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Customer not found")

        return {
            "id": result["id"],
            "name": result["name"],
            "company": result["company"],
            "email": result["email"]
        }

    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()



# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel
# from fastapi.security import OAuth2PasswordRequestForm
# from passlib.context import CryptContext
#
# router = APIRouter()
#
# # Simulace přístupu k databázi (nahradit reálnou implementací)
# MOCK_CUSTOMERS = {
#     "example_user": {
#         "password_hash": "$2b$12$EIXnZaV5l0TnRIRhTbuvSOb7DT4OQl.d6liICZGpG2daLaJGV4Us2",  # bcrypt hash hesla "example_password"
#         "customer_id": 1,
#         "company": "Example Corp",
#         "monthly_tokens": 100,
#         "remaining_tokens": 50,
#         "visible": 1,
#     }
# }
#
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
#
#
# class LoginRequest(BaseModel):
#     username: str
#     password: str
#
#
# class LoginResponse(BaseModel):
#     customer_id: int
#     name: str
#     company: str
#     monthly_tokens: int
#     remaining_tokens: int
#
#
# @router.post("/login", response_model=LoginResponse)
# async def login(data: LoginRequest):
#     user = MOCK_CUSTOMERS.get(data.username)
#     if not user or not user["visible"]:
#         raise HTTPException(status_code=401, detail="User not found or inactive")
#
#     if not pwd_context.verify(data.password, user["password_hash"]):
#         raise HTTPException(status_code=401, detail="Invalid password")
#
#     return {
#         "customer_id": user["customer_id"],
#         "name": data.username,
#         "company": user["company"],
#         "monthly_tokens": user["monthly_tokens"],
#         "remaining_tokens": user["remaining_tokens"],
#     }
