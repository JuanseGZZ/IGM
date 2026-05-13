from fastapi import APIRouter
from .dto import StateDTO
from .service import ProductService

router = APIRouter()
_service = ProductService()


@router.get("/state", response_model=StateDTO)
def bring():
    return _service.bring()


@router.put("/state", status_code=204)
def save(state: StateDTO):
    _service.save(state)
