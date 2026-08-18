from fastapi import FastAPI
from database import Base, engine
import models
import socket

from routes import users, products, orders

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(users.router)
app.include_router(products.router)
app.include_router(orders.router)


@app.get("/")
def root():
    return {"message": "ShopKart API"}

@app.get("/whoami")
def whoami():
    return {
        "hostname": socket.gethostname()
    }

@app.get("/health")
def health():
    return {"status": "ok"}