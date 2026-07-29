from fastapi import APIRouter

router = APIRouter(prefix="/orders")


@router.post("/")
def create_order():

    return {
        "message": "Order Created"
    }


@router.get("/")
def get_orders():

    return [
        {
            "id": 1,
            "product": "Laptop",
            "quantity": 1
        }
    ]