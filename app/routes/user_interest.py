from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_mysql_session
from app.repositories.user_interest_repository import UserInterestRepository
from app.schemas import UserInterestCreate, UserInterestResponse, MessageResponse
from app.util.log import get_logger

logger = get_logger(__name__)
router = APIRouter()


def get_interest_repository(
    db: Session = Depends(get_mysql_session),
) -> UserInterestRepository:
    """Dependency to get user interest repository"""
    return UserInterestRepository(db)


@router.post(
    "/users/{user_id}/interests",
    response_model=UserInterestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user interest",
    description="Create a new interest for a specific user",
)
async def create_user_interest(
    user_id: int,
    interest_data: UserInterestCreate,
    interest_repo: UserInterestRepository = Depends(get_interest_repository),
):
    """
    Create a new interest for a user.

    - **user_id**: The ID of the user
    - **field_of_study**: Field of study the user is interested in
    - **interest_level**: Level of interest (low, medium, high)
    """
    try:
        interest = interest_repo.create_interest(user_id, interest_data)
        logger.info(f"Interest created successfully for user {user_id}")
        return interest

    except ValueError as e:
        logger.warning(f"Interest creation failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating interest: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while creating interest",
        )


@router.get(
    "/users/{user_id}/interests",
    response_model=List[UserInterestResponse],
    summary="Get user interests",
    description="Retrieve all interests for a specific user",
)
async def get_user_interests(
    user_id: int,
    interest_repo: UserInterestRepository = Depends(get_interest_repository),
):
    """
    Get all interests for a specific user.

    - **user_id**: The ID of the user
    """
    try:
        interests = interest_repo.get_interests_by_user(user_id)
        return interests

    except Exception as e:
        logger.error(f"Unexpected error retrieving interests for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving interests",
        )


@router.get(
    "/interests/{interest_id}",
    response_model=UserInterestResponse,
    summary="Get interest by ID",
    description="Retrieve a specific interest by its ID",
)
async def get_interest(
    interest_id: int,
    interest_repo: UserInterestRepository = Depends(get_interest_repository),
):
    """
    Get a specific interest by its ID.

    - **interest_id**: The ID of the interest to retrieve
    """
    try:
        interest = interest_repo.get_interest_by_id(interest_id)
        if not interest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Interest not found"
            )

        return interest

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving interest {interest_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving interest",
        )


@router.delete(
    "/interests/{interest_id}",
    response_model=MessageResponse,
    summary="Delete interest",
    description="Delete a specific interest",
)
async def delete_interest(
    interest_id: int,
    interest_repo: UserInterestRepository = Depends(get_interest_repository),
):
    """
    Delete a specific interest.

    - **interest_id**: The ID of the interest to delete
    """
    try:
        success = interest_repo.delete_interest(interest_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Interest not found"
            )

        logger.info(f"Interest deleted: {interest_id}")
        return MessageResponse(message="Interest deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting interest {interest_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while deleting interest",
        )
