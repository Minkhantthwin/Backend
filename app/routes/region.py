from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_mysql_session
from app.dependencies.auth import require_admin
from app.repositories.region_repository import RegionRepository
from app.schemas import RegionCreate, RegionResponse, MessageResponse
from app.util.log import get_logger

logger = get_logger(__name__)
router = APIRouter()


def get_region_repository(db: Session = Depends(get_mysql_session)) -> RegionRepository:
    return RegionRepository(db)


@router.post(
    "/regions",
    response_model=RegionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new region",
    description="Create a new region (country)",
)
async def create_region(
    region_data: RegionCreate,
    region_repo: RegionRepository = Depends(get_region_repository),
    current_admin=Depends(require_admin),
):
    try:
        region = region_repo.create_region(region_data)
        logger.info(f"Region created successfully: {region.name}")
        return region
    except ValueError as e:
        logger.warning(f"Region creation failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating region: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while creating region",
        )


@router.get(
    "/regions/{region_id}",
    response_model=RegionResponse,
    summary="Get region by ID",
    description="Retrieve a specific region by its ID",
)
async def get_region(
    region_id: int,
    region_repo: RegionRepository = Depends(get_region_repository),
    current_admin=Depends(require_admin),
):
    try:
        region = region_repo.get_region_by_id(region_id)
        if not region:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Region not found"
            )
        return region
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving region {region_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving region",
        )


@router.get(
    "/regions",
    response_model=List[RegionResponse],
    summary="Get list of regions",
    description="Retrieve a list of regions (admin only, paginated client-side).",
)
async def get_regions(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(100, ge=1, le=100, description="Number of regions per page"),
    region_repo: RegionRepository = Depends(get_region_repository),
    current_admin=Depends(require_admin),
):
    try:
        skip = (page - 1) * per_page
        regions = region_repo.get_regions(skip=skip, limit=per_page)
        return regions
    except Exception as e:
        logger.error(f"Unexpected error retrieving regions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving regions",
        )


@router.get(
    "/regions/search",
    response_model=List[RegionResponse],
    summary="Search regions",
    description="Search regions by name or code (case-insensitive)",
)
async def search_regions(
    query: str = Query(..., min_length=1, description="Partial name or code"),
    limit: int = Query(50, ge=1, le=100),
    region_repo: RegionRepository = Depends(get_region_repository),
    current_admin=Depends(require_admin),
):
    try:
        results = region_repo.search_regions(query, limit=limit)
        return results
    except Exception as e:
        logger.error(f"Unexpected error searching regions '{query}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while searching regions",
        )


@router.put(
    "/regions/{region_id}",
    response_model=RegionResponse,
    summary="Update region",
    description="Update region information",
)
async def update_region(
    region_id: int,
    region_data: RegionCreate,
    region_repo: RegionRepository = Depends(get_region_repository),
    current_admin=Depends(require_admin),
):
    try:
        region = region_repo.update_region(region_id, region_data)
        if not region:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Region not found"
            )
        logger.info(f"Region updated successfully: {region.name}")
        return region
    except ValueError as e:
        logger.warning(f"Region update failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating region {region_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while updating region",
        )


@router.delete(
    "/regions/{region_id}",
    response_model=MessageResponse,
    summary="Delete region",
    description="Delete a specific region",
)
async def delete_region(
    region_id: int,
    region_repo: RegionRepository = Depends(get_region_repository),
    current_admin=Depends(require_admin),
):
    try:
        success = region_repo.delete_region(region_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Region not found"
            )
        logger.info(f"Region deleted: {region_id}")
        return MessageResponse(message="Region deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting region {region_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while deleting region",
        )
