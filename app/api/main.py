from fastapi import FastAPI
from api.routes import router  # Nastavení routeru

app = FastAPI()

app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "Hello, API is running!"}