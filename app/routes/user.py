from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
import math

from app.database import get_mysql_session
from app.repositories.user_repository import UserRepository
from app.schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    MessageResponse,
    RecommendationListResponse,
)
from app.dependencies.auth import get_current_user, get_optional_current_user
from app.models import User
from app.util.log import get_logger

logger = get_logger(__name__)
router = APIRouter()


def get_user_repository(db: Session = Depends(get_mysql_session)) -> UserRepository:
    """Dependency to get user repository"""
    return UserRepository(db)


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="""             
             Create a new university.
             
             **Example Request Body:**
             ```json
            {
                "email": "john.doe@example.com",
                "password": "StrongPassword123!",
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1234567890",
                "date_of_birth": "1990-01-01",
                "nationality": "American",
                "interests": [
                    {
                    "field_of_study": "Artificial Intelligence",
                    "interest_level": "high"
                    }
                ],
                "test_scores": [
                    {
                    "test_type": "GRE",
                    "score": "330",
                    "max_score": "340",
                    "test_date": "2022-08-15",
                    "expiry_date": "2027-08-15"
                    }
                ]
                }
                            ```
                            """,
)
async def create_user(
    user_data: UserCreate, user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Create a new user with the following information:

    - **email**: User's email address (must be unique)
    - **password**: User's password (minimum 8 characters)
    - **first_name**: User's first name
    - **last_name**: User's last name
    - **phone**: Optional phone number
    - **date_of_birth**: Optional date of birth
    - **nationality**: Optional nationality
    - **qualifications**: Optional list of user qualifications
    - **interests**: Optional list of user interests
    - **test_scores**: Optional list of test scores
    """
    try:
        # Check if user already exists
        existing_user = user_repo.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

        # Create user
        user = user_repo.create_user(user_data)
        logger.info(f"User created successfully: {user.email}")

        return user

    except ValueError as e:
        logger.warning(f"User creation failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while creating user",
        )


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="Retrieve a specific user by their ID",
)
async def get_user(
    user_id: int, user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Get a specific user by their ID.

    - **user_id**: The ID of the user to retrieve
    """
    try:
        user = user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving user",
        )


@router.get(
    "/users",
    response_model=UserListResponse,
    summary="Get list of users",
    description="Retrieve a paginated list of users.",
)
async def get_users(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Number of users per page"),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Get a paginated list of users.

    - **page**: Page number (starts from 1)
    - **per_page**: Number of users per page (1-100)
    """
    try:
        skip = (page - 1) * per_page

        users = user_repo.get_users(skip=skip, limit=per_page)
        total_users = user_repo.count_users()
        total_pages = math.ceil(total_users / per_page)

        return UserListResponse(
            users=users,
            total=total_users,
            page=page,
            per_page=per_page,
            pages=total_pages,
        )

    except Exception as e:
        logger.error(f"Unexpected error retrieving users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving users",
        )


@router.put(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Update user",
    description="Update user information",
)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Update user information.

    - **user_id**: The ID of the user to update
    - All fields are optional and only provided fields will be updated
    """
    try:
        user = user_repo.update_user(user_id, user_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        logger.info(f"User updated successfully: {user.email}")
        return user

    except ValueError as e:
        logger.warning(f"User update failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while updating user",
        )


@router.delete(
    "/users/{user_id}",
    response_model=MessageResponse,
    summary="Delete user",
    description="Permanently delete a user",
)
async def delete_user(
    user_id: int, user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Permanently delete a user.

    - **user_id**: The ID of the user to delete
    """
    try:
        success = user_repo.delete_user(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        logger.info(f"User deleted: {user_id}")
        return MessageResponse(message="User deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while deleting user",
        )


# Remove the verify_user endpoint since is_verified doesn't exist in the model


@router.get(
    "/users/search/email/{email}",
    response_model=UserResponse,
    summary="Get user by email",
    description="Retrieve a user by their email address",
)
async def get_user_by_email(
    email: str, user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Get a user by their email address.

    - **email**: The email address of the user to retrieve
    """
    try:
        user = user_repo.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving user by email {email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving user",
        )


@router.get(
    "/users/{user_id}/recommendations",
    response_model=List[dict],
    summary="Get user recommendations",
    description="Get personalized program recommendations for a user (requires authentication)",
)
async def get_user_recommendations(
    user_id: int,
    current_user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Get personalized program recommendations for a user.

    **Requires Authentication:** Users can only access their own recommendations
    unless they have admin privileges.

    - **user_id**: The ID of the user to get recommendations for
    """
    try:
        # Check if user is accessing their own data (basic authorization)
        if current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own recommendations",
            )

        # Check if user exists
        target_user = user_repo.get_user_by_id(user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Get recommendations from Neo4j
        recommendations = user_repo.get_user_recommendations(user_id, limit=10)

        logger.info(
            f"Retrieved {len(recommendations)} recommendations for user {user_id}"
        )
        return recommendations

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error getting recommendations for user {user_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while getting recommendations",
        )
