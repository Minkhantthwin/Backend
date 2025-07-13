from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
import math

from app.database import get_mysql_session
from app.repositories.program import ProgramRepository
from app.schemas import ProgramCreate, ProgramResponse, MessageResponse
from app.util.log import get_logger

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
    program_repo: ProgramRepository = Depends(get_program_repository),
):
    """
    Get a paginated list of programs.

    - **page**: Page number (starts from 1)
    - **per_page**: Number of programs per page (1-100)
    - **active_only**: Whether to include only active programs
    """
    try:
        skip = (page - 1) * per_page

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
