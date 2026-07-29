from fastapi import APIRouter

router = APIRouter(prefix="/users")


@router.post("/register")
def register():

    return {
        "message": "User Registered"
    }


@router.post("/login")
def login():

    return {
        "token": "sample-token"
    }