from fastapi import APIRouter

router = APIRouter(prefix="/products")


@router.get("/")
def get_products():

    return [
        {
            "id": 1,
            "name": "Laptop",
            "price": 60000
        },
        {
            "id": 2,
            "name": "Mouse",
            "price": 800
        }
    ]