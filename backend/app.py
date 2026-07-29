from fastapi import FastAPI

from routes import users
from routes import products
from routes import orders

app = FastAPI()

app.include_router(users.router)
app.include_router(products.router)
app.include_router(orders.router)


@app.get("/")
def root():
    return {"message": "ShopKart API"}