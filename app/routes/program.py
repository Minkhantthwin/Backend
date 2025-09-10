from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
import math

from app.database import get_mysql_session
from app.repositories.program import ProgramRepository
from app.schemas import ProgramCreate, ProgramResponse, MessageResponse
from app.util.log import get_logger
from app.dependencies.auth import require_admin

logger = get_logger(__name__)
router = APIRouter()


def get_program_repository(
    db: Session = Depends(get_mysql_session),
) -> ProgramRepository:
    """Dependency to get program repository"""
    return ProgramRepository(db)


@router.post(
    "/programs",
    response_model=ProgramResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new program",
    description="Create a new program with requirements",
)
async def create_program(
    program_data: ProgramCreate,
    program_repo: ProgramRepository = Depends(get_program_repository),
):
    """
    Create a new program with the following information:

    - **university_id**: ID of the university offering the program
    - **name**: Name of the program
    - **degree_level**: Level of degree (bachelor, master, phd, etc.)
    - **field_of_study**: Field of study
    - **duration_years**: Duration in years
    - **language**: Language of instruction
    - **tuition_fee**: Tuition fee amount
    - **currency**: Currency of tuition fee
    - **application_deadline**: Application deadline date
    - **start_date**: Program start date
    - **description**: Program description
    - **requirements**: List of program requirements
    """
    try:
        program = program_repo.create_program(program_data)
        logger.info(f"Program created successfully: {program.name}")
        return program

    except ValueError as e:
        logger.warning(f"Program creation failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating program: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while creating program",
        )


@router.get(
    "/programs/count",
    summary="Program counts",
    description="Get total and active program counts (admin only)",
)
async def program_counts(
    program_repo: ProgramRepository = Depends(get_program_repository),
    current_admin=Depends(require_admin),
):
    try:
        active = program_repo.count_programs(active_only=True)
        total = program_repo.count_programs(active_only=False)
        return {"total": total, "active": active}
    except Exception as e:
        logger.error(f"Unexpected error retrieving program counts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error retrieving program counts",
        )


@router.get(
    "/programs/top-ranked",
    summary="Programs from highest ranking universities",
    description="List programs offered by the top N world-ranked universities (public)",
)
async def get_programs_from_top_ranked_unis(
    top_universities: int = Query(
        10, ge=1, le=100, description="Number of top universities to include"
    ),
    per_university: int = Query(
        5, ge=1, le=50, description="Max programs per university"
    ),
    program_repo: ProgramRepository = Depends(get_program_repository),
):
    """Return programs offered by top ranked universities (static route placed before /programs/{program_id} to avoid 422)."""
    try:
        data = program_repo.get_programs_from_top_ranked_universities(
            top_n_universities=top_universities, limit_per_university=per_university
        )
        return {
            "top_universities": top_universities,
            "per_university": per_university,
            "total_programs": len(data),
            "programs": data,
        }
    except Exception as e:
        logger.error(f"Unexpected error retrieving top-ranked university programs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving top ranked programs",
        )


@router.get(
    "/programs/{program_id}",
    response_model=ProgramResponse,
    summary="Get program by ID",
    description="Retrieve a specific program by its ID",
)
async def get_program(
    program_id: int, program_repo: ProgramRepository = Depends(get_program_repository)
):
    """
    Get a specific program by its ID.

    - **program_id**: The ID of the program to retrieve
    """
    try:
        program = program_repo.get_program_by_id(program_id)
        if not program:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Program not found"
            )

        return program

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving program {program_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving program",
        )


@router.get(
    "/programs",
    response_model=List[ProgramResponse],
    summary="Get list of programs",
    description="Retrieve a paginated list of programs",
)
async def get_programs(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Number of programs per page"),
    active_only: bool = Query(True, description="Only return active programs"),
    search: str = Query(
        None, description="Search programs by name, field, or university"
    ),
    program_repo: ProgramRepository = Depends(get_program_repository),
):
    """
    Get a paginated list of programs with optional search.

    - **page**: Page number (starts from 1)
    - **per_page**: Number of programs per page (1-100)
    - **active_only**: Whether to include only active programs
    - **search**: Search term to filter programs by name, field of study, or university name
    """
    try:
        skip = (page - 1) * per_page

        if search:
            # Use search method when search query is provided
            programs = program_repo.search_programs(
                search_query=search, skip=skip, limit=per_page, active_only=active_only
            )
        else:
            # Use regular get_programs when no search query
            programs = program_repo.get_programs(
                skip=skip, limit=per_page, active_only=active_only
            )
        return programs

    except Exception as e:
        logger.error(f"Unexpected error retrieving programs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving programs",
        )


@router.get(
    "/universities/{university_id}/programs",
    response_model=List[ProgramResponse],
    summary="Get programs by university",
    description="Retrieve all programs for a specific university",
)
async def get_programs_by_university(
    university_id: int,
    program_repo: ProgramRepository = Depends(get_program_repository),
):
    """
    Get all programs for a specific university.

    - **university_id**: The ID of the university
    """
    try:
        programs = program_repo.get_programs_by_university(university_id)
        return programs

    except Exception as e:
        logger.error(
            f"Unexpected error retrieving programs for university {university_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving programs",
        )


@router.get(
    "/programs/search/field/{field_of_study}",
    response_model=List[ProgramResponse],
    summary="Search programs by field",
    description="Search programs by field of study",
)
async def search_programs_by_field(
    field_of_study: str,
    program_repo: ProgramRepository = Depends(get_program_repository),
):
    """
    Search programs by field of study.

    - **field_of_study**: The field of study to search for
    """
    try:
        programs = program_repo.get_programs_by_field(field_of_study)
        return programs

    except Exception as e:
        logger.error(
            f"Unexpected error searching programs by field {field_of_study}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while searching programs",
        )


@router.delete(
    "/programs/{program_id}",
    response_model=MessageResponse,
    summary="Delete program",
    description="Soft delete a program (deactivate)",
)
async def delete_program(
    program_id: int, program_repo: ProgramRepository = Depends(get_program_repository)
):
    """
    Soft delete a program (set as inactive).

    - **program_id**: The ID of the program to delete
    """
    try:
        success = program_repo.delete_program(program_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Program not found"
            )

        logger.info(f"Program soft deleted: {program_id}")
        return MessageResponse(message="Program deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting program {program_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while deleting program",
        )


@router.put(
    "/programs/{program_id}",
    response_model=ProgramResponse,
    summary="Update program",
    description="Update program details and replace requirements",
)
async def update_program(
    program_id: int,
    program_data: ProgramCreate,
    program_repo: ProgramRepository = Depends(get_program_repository),
):
    """
    Update an existing program with the following information:

    - **name**: Name of the program
    - **degree_level**: Level of degree (bachelor, master, phd, etc.)
    - **field_of_study**: Field of study
    - **duration_years**: Duration in years
    - **language**: Language of instruction
    - **tuition_fee**: Tuition fee amount
    - **currency**: Currency of tuition fee
    - **application_deadline**: Application deadline date
    - **start_date**: Program start date
    - **description**: Program description
    - **requirements**: List of program requirements
    """
    try:
        program = program_repo.update_program(program_id, program_data)
        if not program:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Program not found"
            )
        logger.info(f"Program updated successfully: {program.name}")
        return program
    except ValueError as e:
        logger.warning(f"Program update failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating program {program_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while updating program",
        )
