from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.services.qualification_service import QualificationService
from app.database import get_mysql_session
from app.schemas import QualificationCheckResponse, QualificationSummaryResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def get_qualification_service(
    db: Session = Depends(get_mysql_session),
) -> QualificationService:
    """Get qualification service instance"""
    return QualificationService(db)


@router.post(
    "/users/{user_id}/qualifications/check/{program_id}",
    response_model=dict,
    summary="Check user qualification for specific program",
)
async def check_user_qualification(
    user_id: int,
    program_id: int,
    qualification_service: QualificationService = Depends(get_qualification_service),
):
    """
    Check if a user meets all requirements for a specific program.

    Returns detailed qualification analysis including:
    - Overall qualification status
    - Qualification score (0-100)
    - Missing requirements
    - Detailed requirement analysis
    """
    try:
        result = qualification_service.check_user_qualification(user_id, program_id)

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=result["error"]
            )

        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error checking qualification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/users/{user_id}/qualifications/summary",
    response_model=dict,
    summary="Get user's qualification summary for all programs",
)
async def get_user_qualifications_summary(
    user_id: int,
    qualification_service: QualificationService = Depends(get_qualification_service),
):
    """
    Get a summary of user's qualifications across all programs.

    Returns:
    - Qualified programs
    - Partially qualified programs
    - Not qualified programs
    """
    try:
        result = qualification_service.get_user_qualifications_summary(user_id)
        return result

    except Exception as e:
        logger.error(f"Error getting qualification summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post(
    "/users/{user_id}/qualifications/check-all",
    response_model=List[dict],
    summary="Check user qualification against all programs",
)
async def check_user_against_all_programs(
    user_id: int,
    qualification_service: QualificationService = Depends(get_qualification_service),
):
    """
    Check user's qualification against all active programs.

    This is useful for generating recommendations based on qualification match.
    """
    try:
        results = qualification_service.check_user_against_all_programs(user_id)
        return results

    except Exception as e:
        logger.error(f"Error checking user against all programs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get(
    "/programs/{program_id}/qualified-users",
    response_model=List[dict],
    summary="Get users qualified for a specific program",
)
async def get_qualified_users_for_program(
    program_id: int,
    qualification_service: QualificationService = Depends(get_qualification_service),
):
    """
    Get all users who are qualified for a specific program.

    Useful for admissions processing and analytics.
    """
    try:
        # Implementation would involve querying UserQualificationStatus
        # This is a placeholder - implement as needed
        return {"message": "Feature coming soon"}

    except Exception as e:
        logger.error(f"Error getting qualified users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
