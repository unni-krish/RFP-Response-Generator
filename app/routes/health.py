from fastapi import APIRouter
from app.models.schemas import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Returns the health status of the service."""
    return HealthResponse(status="healthy")
