from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
import math

from app.database import get_mysql_session
from app.repositories.application_repository import ApplicationRepository
from app.schemas import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationResponse,
    MessageResponse,
)
from app.util.log import get_logger
from app.dependencies.auth import require_admin

logger = get_logger(__name__)
router = APIRouter()


def get_application_repository(
    db: Session = Depends(get_mysql_session),
) -> ApplicationRepository:
    """Dependency to get application repository"""
    return ApplicationRepository(db)


@router.post(
    "/applications",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new application",
    description="Create a new application for a program",
)
async def create_application(
    application_data: ApplicationCreate,
    application_repo: ApplicationRepository = Depends(get_application_repository),
):
    """
    Create a new application with the following information:

    - **user_id**: ID of the user applying
    - **program_id**: ID of the program being applied to
    - **personal_statement**: Personal statement for the application
    - **additional_documents**: Additional documents (JSON format)
    """
    try:
        application = application_repo.create_application(application_data)
        logger.info(
            f"Application created successfully for user {application_data.user_id}"
        )
        return application

    except ValueError as e:
        logger.warning(f"Application creation failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating application: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while creating application",
        )


@router.get(
    "/applications/stats",
    summary="Application statistics",
    description="Get counts of applications by status (admin only)",
)
async def application_stats(
    application_repo: ApplicationRepository = Depends(get_application_repository),
    current_admin=Depends(require_admin),
):
    try:
        return application_repo.get_status_counts()
    except Exception as e:
        logger.error(f"Unexpected error retrieving application stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error retrieving application stats",
        )


@router.get(
    "/applications/{application_id}",
    response_model=ApplicationResponse,
    summary="Get application by ID",
    description="Retrieve a specific application by its ID",
)
async def get_application(
    application_id: int,
    application_repo: ApplicationRepository = Depends(get_application_repository),
):
    """
    Get a specific application by its ID.

    - **application_id**: The ID of the application to retrieve
    """
    try:
        application = application_repo.get_application_by_id(application_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
            )

        return application

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving application {application_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving application",
        )


@router.get(
    "/users/{user_id}/applications",
    response_model=List[ApplicationResponse],
    summary="Get applications by user",
    description="Retrieve all applications for a specific user",
)
async def get_applications_by_user(
    user_id: int,
    application_repo: ApplicationRepository = Depends(get_application_repository),
):
    """
    Get all applications for a specific user.

    - **user_id**: The ID of the user
    """
    try:
        applications = application_repo.get_applications_by_user(user_id)
        return applications

    except Exception as e:
        logger.error(
            f"Unexpected error retrieving applications for user {user_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving applications",
        )


@router.get(
    "/programs/{program_id}/applications",
    response_model=List[ApplicationResponse],
    summary="Get applications by program",
    description="Retrieve all applications for a specific program",
)
async def get_applications_by_program(
    program_id: int,
    application_repo: ApplicationRepository = Depends(get_application_repository),
):
    """
    Get all applications for a specific program.

    - **program_id**: The ID of the program
    """
    try:
        applications = application_repo.get_applications_by_program(program_id)
        return applications

    except Exception as e:
        logger.error(
            f"Unexpected error retrieving applications for program {program_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving applications",
        )


@router.get(
    "/applications",
    response_model=List[ApplicationResponse],
    summary="Get list of applications",
    description="Retrieve a paginated list of applications",
)
async def get_applications(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(
        10, ge=1, le=100, description="Number of applications per page"
    ),
    application_repo: ApplicationRepository = Depends(get_application_repository),
):
    """
    Get a paginated list of applications.

    - **page**: Page number (starts from 1)
    - **per_page**: Number of applications per page (1-100)
    """
    try:
        skip = (page - 1) * per_page

        applications = application_repo.get_applications(skip=skip, limit=per_page)
        return applications

    except Exception as e:
        logger.error(f"Unexpected error retrieving applications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving applications",
        )


@router.put(
    "/applications/{application_id}",
    response_model=ApplicationResponse,
    summary="Update application",
    description="Update application information",
)
async def update_application(
    application_id: int,
    application_data: ApplicationUpdate,
    application_repo: ApplicationRepository = Depends(get_application_repository),
):
    """
    Update application information.

    - **application_id**: The ID of the application to update
    - All fields are optional and only provided fields will be updated
    """
    try:
        application = application_repo.update_application(
            application_id, application_data
        )
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
            )

        logger.info(f"Application updated successfully: {application_id}")
        return application

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating application {application_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while updating application",
        )


@router.delete(
    "/applications/{application_id}",
    response_model=MessageResponse,
    summary="Delete application",
    description="Delete a specific application",
)
async def delete_application(
    application_id: int,
    application_repo: ApplicationRepository = Depends(get_application_repository),
):
    """
    Delete a specific application.

    - **application_id**: The ID of the application to delete
    """
    try:
        success = application_repo.delete_application(application_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
            )

        logger.info(f"Application deleted: {application_id}")
        return MessageResponse(message="Application deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting application {application_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while deleting application",
        )
