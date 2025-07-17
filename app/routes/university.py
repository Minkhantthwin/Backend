from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_mysql_session
from app.repositories.university_repository import UniversityRepository
from app.schemas import UniversityCreate, UniversityResponse, MessageResponse
from app.util.log import get_logger

logger = get_logger(__name__)
router = APIRouter()


def get_university_repository(
    db: Session = Depends(get_mysql_session),
) -> UniversityRepository:
    return UniversityRepository(db)


@router.post(
    "/universities",
    response_model=UniversityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new university",
    description="""
             Create a new university.
             
             **Example Request Body:**
             ```json
             {
                 "name": "Harvard University",
                 "region_id": 1,
                 "city": "Cambridge",
                 "established_year": 1636,
                 "type": "Private",
                 "website": "https://www.harvard.edu",
                 "description": "Harvard University is a private Ivy League research university in Cambridge, Massachusetts.",
                 "ranking_world": 3,
                 "ranking_national": 2
             }
             ```
             """,
)
async def create_university(
    university_data: UniversityCreate,
    university_repo: UniversityRepository = Depends(get_university_repository),
):
    try:
        university = university_repo.create_university(university_data)
        logger.info(f"University created successfully: {university.name}")
        return university
    except ValueError as e:
        logger.warning(f"University creation failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating university: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while creating university",
        )


@router.get(
    "/universities/{university_id}",
    response_model=UniversityResponse,
    summary="Get university by ID",
    description="Retrieve a specific university by its ID",
)
async def get_university(
    university_id: int,
    university_repo: UniversityRepository = Depends(get_university_repository),
):
    try:
        university = university_repo.get_university_by_id(university_id)
        if not university:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="University not found"
            )
        return university
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving university {university_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving university",
        )


@router.get(
    "/universities",
    response_model=List[UniversityResponse],
    summary="Get list of universities",
    description="Retrieve a paginated list of universities with optional filtering by region",
)
async def get_universities(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(
        10, ge=1, le=100, description="Number of universities per page"
    ),
    region_id: Optional[int] = Query(None, description="Filter by region ID"),
    university_repo: UniversityRepository = Depends(get_university_repository),
):
    try:
        skip = (page - 1) * per_page
        universities = university_repo.get_universities(
            skip=skip, limit=per_page, region_id=region_id
        )
        return universities
    except Exception as e:
        logger.error(f"Unexpected error retrieving universities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving universities",
        )


@router.get(
    "/universities/search",
    response_model=List[UniversityResponse],
    summary="Search universities by name",
    description="Search for universities by name (case-insensitive partial match)",
)
async def search_universities(
    name: str = Query(..., description="University name to search for"),
    university_repo: UniversityRepository = Depends(get_university_repository),
):
    try:
        universities = university_repo.search_universities_by_name(name)
        return universities
    except Exception as e:
        logger.error(f"Unexpected error searching universities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while searching universities",
        )


@router.put(
    "/universities/{university_id}",
    response_model=UniversityResponse,
    summary="Update university",
    description="""
            Update university information.
            
            **Example Request Body:**
            ```json
            {
                "name": "Harvard University",
                "region_id": 1,
                "city": "Cambridge",
                "established_year": 1636,
                "type": "Private",
                "website": "https://www.harvard.edu",
                "description": "Harvard University is a private Ivy League research university in Cambridge, Massachusetts. Updated description.",
                "ranking_world": 2,
                "ranking_national": 1
            }
            ```
            """,
)
async def update_university(
    university_id: int,
    university_data: UniversityCreate,
    university_repo: UniversityRepository = Depends(get_university_repository),
):
    try:
        university = university_repo.update_university(university_id, university_data)
        if not university:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="University not found"
            )
        logger.info(f"University updated successfully: {university.name}")
        return university
    except ValueError as e:
        logger.warning(f"University update failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating university {university_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while updating university",
        )


@router.delete(
    "/universities/{university_id}",
    response_model=MessageResponse,
    summary="Delete university",
    description="Delete a specific university",
)
async def delete_university(
    university_id: int,
    university_repo: UniversityRepository = Depends(get_university_repository),
):
    try:
        success = university_repo.delete_university(university_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="University not found"
            )
        logger.info(f"University deleted: {university_id}")
        return MessageResponse(message="University deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting university {university_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while deleting university",
        )


@router.get(
    "/regions/{region_id}/universities",
    response_model=List[dict],
    summary="Get universities by region from Neo4j",
    description="Get universities in a specific region using Neo4j graph relationships",
)
async def get_universities_by_region_neo4j(
    region_id: int,
    university_repo: UniversityRepository = Depends(get_university_repository),
):
    """
    Get universities in a specific region using Neo4j graph data.
    
    This endpoint leverages Neo4j relationships to find universities in a region.
    
    - **region_id**: The ID of the region to get universities for
    """
    try:
        universities = university_repo.get_universities_by_region_neo4j(region_id)
        
        return {
            "region_id": region_id,
            "universities": universities,
            "total_universities": len(universities)
        }
        
    except Exception as e:
        logger.error(f"Unexpected error getting universities by region: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while getting universities",
        )
