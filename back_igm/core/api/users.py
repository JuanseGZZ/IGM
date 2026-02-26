from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from service import test

router = APIRouter(prefix="/api/users", tags=["users"])

# Modelo
class User(BaseModel):
    id: int
    name: str
    email: str

# Fake DB
users_db: List[User] = []

@router.get("/", response_model=List[User])
def list_users():
    return users_db

@router.get("/{user_id}", response_model=User)
def get_user(user_id: int):
    for user in users_db:
        if user.id == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")

@router.post("/", response_model=User)
def create_user(user: User):
    users_db.append(user)
    return user