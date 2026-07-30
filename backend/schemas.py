from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    price: int
    quantity: int


class ProductResponse(ProductCreate):
    id: int

    class Config:
        from_attributes = True