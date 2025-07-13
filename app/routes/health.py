from fastapi import APIRouter, status
from app.database import get_database_manager
from app.util.log import get_logger
from pydantic import BaseModel

logger = get_logger(__name__)
router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response schema"""

    status: str
    message: str
    database_status: dict


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check the health status of the application and databases",
)
async def health_check():
    """
    Health check endpoint to verify application and database status.

    Returns:
    - Application status
    - Database connection status for MySQL and Neo4j
    """
    try:
        db_manager = get_database_manager()

        # Test database connections
        db_status = db_manager.test_all_connections()

        # Determine overall status
        all_healthy = all(db_status.values())
        overall_status = "healthy" if all_healthy else "degraded"
        message = (
            "All systems operational"
            if all_healthy
            else "Some services experiencing issues"
        )

        return HealthResponse(
            status=overall_status, message=message, database_status=db_status
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            message="System experiencing issues",
            database_status={"mysql": False, "neo4j": False},
        )
