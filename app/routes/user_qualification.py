from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_mysql_session
from app.repositories.user_qualification import UserQualificationRepository
from app.schemas import (
    UserQualificationCreate,
    UserQualificationResponse,
    MessageResponse,
)
from app.util.log import get_logger

logger = get_logger(__name__)
router = APIRouter()


def get_qualification_repository(
    db: Session = Depends(get_mysql_session),
) -> UserQualificationRepository:
    """Dependency to get user qualification repository"""
    return UserQualificationRepository(db)


@router.post(
    "/users/{user_id}/qualifications",
    response_model=UserQualificationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user qualification",
    description="Create a new qualification for a specific user",
)
async def create_user_qualification(
    user_id: int,
    qualification_data: UserQualificationCreate,
    qualification_repo: UserQualificationRepository = Depends(
        get_qualification_repository
    ),
):
    """
    Create a new qualification for a user.

    - **user_id**: The ID of the user
    - **qualification_type**: Type of qualification (high_school, bachelor, master, etc.)
    - **institution_name**: Name of the institution
    - **degree_name**: Name of the degree
    - **field_of_study**: Field of study
    - **grade_point**: Grade point achieved
    - **max_grade_point**: Maximum possible grade point
    - **completion_year**: Year of completion
    - **country**: Country where qualification was obtained
    - **is_completed**: Whether the qualification is completed
    """
    try:
        qualification = qualification_repo.create_qualification(
            user_id, qualification_data
        )
        logger.info(f"Qualification created successfully for user {user_id}")
        return qualification

    except ValueError as e:
        logger.warning(f"Qualification creation failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating qualification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while creating qualification",
        )


@router.get(
    "/users/{user_id}/qualifications",
    response_model=List[UserQualificationResponse],
    summary="Get user qualifications",
    description="Retrieve all qualifications for a specific user",
)
async def get_user_qualifications(
    user_id: int,
    qualification_repo: UserQualificationRepository = Depends(
        get_qualification_repository
    ),
):
    """
    Get all qualifications for a specific user.

    - **user_id**: The ID of the user
    """
    try:
        qualifications = qualification_repo.get_qualifications_by_user(user_id)
        return qualifications

    except Exception as e:
        logger.error(
            f"Unexpected error retrieving qualifications for user {user_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving qualifications",
        )


@router.get(
    "/qualifications/{qualification_id}",
    response_model=UserQualificationResponse,
    summary="Get qualification by ID",
    description="Retrieve a specific qualification by its ID",
)
async def get_qualification(
    qualification_id: int,
    qualification_repo: UserQualificationRepository = Depends(
        get_qualification_repository
    ),
):
    """
    Get a specific qualification by its ID.

    - **qualification_id**: The ID of the qualification to retrieve
    """
    try:
        qualification = qualification_repo.get_qualification_by_id(qualification_id)
        if not qualification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Qualification not found"
            )

        return qualification

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error retrieving qualification {qualification_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving qualification",
        )


@router.delete(
    "/qualifications/{qualification_id}",
    response_model=MessageResponse,
    summary="Delete qualification",
    description="Delete a specific qualification",
)
async def delete_qualification(
    qualification_id: int,
    qualification_repo: UserQualificationRepository = Depends(
        get_qualification_repository
    ),
):
    """
    Delete a specific qualification.

    - **qualification_id**: The ID of the qualification to delete
    """
    try:
        success = qualification_repo.delete_qualification(qualification_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Qualification not found"
            )

        logger.info(f"Qualification deleted: {qualification_id}")
        return MessageResponse(message="Qualification deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting qualification {qualification_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while deleting qualification",
        )
