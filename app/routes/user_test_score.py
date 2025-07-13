from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_mysql_session
from app.repositories.user_test_score import UserTestScoreRepository
from app.schemas import UserTestScoreCreate, UserTestScoreResponse, MessageResponse
from app.util.log import get_logger

logger = get_logger(__name__)
router = APIRouter()


def get_test_score_repository(
    db: Session = Depends(get_mysql_session),
) -> UserTestScoreRepository:
    """Dependency to get user test score repository"""
    return UserTestScoreRepository(db)


@router.post(
    "/users/{user_id}/test-scores",
    response_model=UserTestScoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user test score",
    description="Create a new test score for a specific user",
)
async def create_user_test_score(
    user_id: int,
    test_score_data: UserTestScoreCreate,
    test_score_repo: UserTestScoreRepository = Depends(get_test_score_repository),
):
    """
    Create a new test score for a user.

    - **user_id**: The ID of the user
    - **test_type**: Type of test (IELTS, TOEFL, GRE, GMAT, etc.)
    - **score**: Score achieved
    - **max_score**: Maximum possible score
    - **test_date**: Date when the test was taken
    - **expiry_date**: Date when the test score expires
    """
    try:
        test_score = test_score_repo.create_test_score(user_id, test_score_data)
        logger.info(f"Test score created successfully for user {user_id}")
        return test_score

    except ValueError as e:
        logger.warning(f"Test score creation failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating test score: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while creating test score",
        )


@router.get(
    "/users/{user_id}/test-scores",
    response_model=List[UserTestScoreResponse],
    summary="Get user test scores",
    description="Retrieve all test scores for a specific user",
)
async def get_user_test_scores(
    user_id: int,
    test_score_repo: UserTestScoreRepository = Depends(get_test_score_repository),
):
    """
    Get all test scores for a specific user.

    - **user_id**: The ID of the user
    """
    try:
        test_scores = test_score_repo.get_test_scores_by_user(user_id)
        return test_scores

    except Exception as e:
        logger.error(f"Unexpected error retrieving test scores for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving test scores",
        )


@router.get(
    "/test-scores/{test_score_id}",
    response_model=UserTestScoreResponse,
    summary="Get test score by ID",
    description="Retrieve a specific test score by its ID",
)
async def get_test_score(
    test_score_id: int,
    test_score_repo: UserTestScoreRepository = Depends(get_test_score_repository),
):
    """
    Get a specific test score by its ID.

    - **test_score_id**: The ID of the test score to retrieve
    """
    try:
        test_score = test_score_repo.get_test_score_by_id(test_score_id)
        if not test_score:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Test score not found"
            )

        return test_score

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving test score {test_score_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving test score",
        )


@router.delete(
    "/test-scores/{test_score_id}",
    response_model=MessageResponse,
    summary="Delete test score",
    description="Delete a specific test score",
)
async def delete_test_score(
    test_score_id: int,
    test_score_repo: UserTestScoreRepository = Depends(get_test_score_repository),
):
    """
    Delete a specific test score.

    - **test_score_id**: The ID of the test score to delete
    """
    try:
        success = test_score_repo.delete_test_score(test_score_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Test score not found"
            )

        logger.info(f"Test score deleted: {test_score_id}")
        return MessageResponse(message="Test score deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting test score {test_score_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while deleting test score",
        )
