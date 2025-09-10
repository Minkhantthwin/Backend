from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_mysql_session
from app.services.recommendation_service import RecommendationService
from app.schemas import RecommendationRequest, RecommendationListResponse, DegreeLevel
from app.dependencies.auth import get_current_user, require_user_or_admin
from app.models import User
from app.util.log import get_logger

logger = get_logger(__name__)
router = APIRouter()


def get_recommendation_service(
    db: Session = Depends(get_mysql_session),
) -> RecommendationService:
    """Dependency to get recommendation service"""
    return RecommendationService(db)


@router.get(
    "/users/{user_id}/recommendations",
    response_model=dict,
    summary="Get comprehensive program recommendations for user",
    description="Get program recommendations based on user interests, qualification status, and test scores",
    operation_id="get_comprehensive_user_recommendations",
)
async def get_user_recommendations(
    user_id: int,
    limit: int = Query(
        10, ge=1, le=50, description="Maximum number of recommendations"
    ),
    current_user: User = Depends(get_current_user),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
):
    """
    Get comprehensive program recommendations for a user.

    This endpoint combines multiple recommendation sources:
    - Interest-based recommendations from user preferences
    - Qualification-based recommendations from assessment results
    - Test score-based recommendations from standardized test results

    **Parameters:**
    - **user_id**: ID of the user to get recommendations for
    - **limit**: Maximum number of recommendations to return (1-50, default: 10)

    **Authentication:** Requires valid JWT token. Users can only access their own recommendations unless they are administrators.
    """
    try:
        # Authorization: user can access own recommendations or admin can access any
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own recommendations",
            )

        recommendations = recommendation_service.get_comprehensive_recommendations(
            user_id=user_id,
            preferred_countries=None,
            preferred_fields=None,
            degree_level=None,
            max_tuition_fee=None,
            language_preference=None,
            limit=limit,
        )

        if "error" in recommendations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=recommendations["error"]
            )

        logger.info(
            f"Generated {len(recommendations.get('recommendations', []))} recommendations for user {user_id}"
        )
        return recommendations

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid parameters for user recommendations: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting user recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while getting recommendations",
        )


@router.get(
    "/users/{user_id}/recommendations/similar-programs",
    response_model=List[dict],
    summary="Get similar program recommendations",
    description="Get program recommendations based on similar characteristics",
)
async def get_similar_program_recommendations(
    user_id: int,
    limit: int = Query(
        10, ge=1, le=50, description="Maximum number of recommendations"
    ),
    current_user: User = Depends(get_current_user),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
):
    """
    Get program recommendations based on similar program characteristics.

    This endpoint finds programs with similar fields and levels to user interests.
    """
    try:
        # Check if user can access this resource
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own recommendations",
            )

        # Get user interests first
        from app.repositories.user_interest_repository import UserInterestRepository
        from app.database import get_mysql_session

        db = next(get_mysql_session())
        interest_repo = UserInterestRepository(db)
        user_interests = interest_repo.get_interests_by_user(user_id)

        if not user_interests:
            return []

        # Get similar programs for each interest field
        all_similar = []
        for interest in user_interests:
            similar = recommendation_service.get_similar_programs_by_field(
                interest.field_of_study, limit=5
            )
            all_similar.extend(similar)

        # Remove duplicates and limit
        seen = set()
        unique_similar = []
        for program in all_similar:
            if program["program_id"] not in seen:
                seen.add(program["program_id"])
                unique_similar.append(program)

        logger.info(f"Found {len(unique_similar)} similar programs for user {user_id}")
        return unique_similar[:limit]

    except Exception as e:
        logger.error(f"Error getting similar program recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while getting similar program recommendations",
        )


@router.get(
    "/recommendations/stats/{user_id}",
    response_model=dict,
    summary="Get recommendation statistics",
    description="Get statistics about available recommendations for a user",
)
async def get_recommendation_stats(
    user_id: int,
    current_user: User = Depends(get_current_user),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
):
    """
    Get statistics about available recommendations for a user.

    This endpoint provides insights into recommendation sources and coverage.
    """
    try:
        # Check if user can access this resource
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own recommendation statistics",
            )

        # Get basic counts from each recommendation source
        interest_recs = recommendation_service._get_interest_based_recommendations(
            user_id, limit=100
        )
        qualification_recs = (
            recommendation_service._get_qualification_based_recommendations(
                user_id, limit=100
            )
        )
        test_score_recs = recommendation_service._get_test_score_based_recommendations(
            user_id, limit=100
        )

        # Safely extract fields with error handling
        def safe_extract_field(recs, field):
            try:
                return [r[field] for r in recs if field in r and r[field]]
            except (KeyError, TypeError):
                return []

        all_recs = interest_recs + qualification_recs + test_score_recs

        stats = {
            "user_id": user_id,
            "recommendation_sources": {
                "interest_based_count": len(interest_recs),
                "qualification_based_count": len(qualification_recs),
                "test_score_based_count": len(test_score_recs),
            },
            "total_unique_programs": len(
                set(safe_extract_field(all_recs, "program_id"))
            ),
            "top_countries": list(set(safe_extract_field(all_recs, "country")))[:10],
            "top_fields": list(set(safe_extract_field(all_recs, "field_of_study")))[
                :10
            ],
            "degree_levels": list(set(safe_extract_field(all_recs, "degree_level"))),
        }

        logger.info(f"Generated recommendation statistics for user {user_id}")
        return stats

    except Exception as e:
        logger.error(f"Error getting recommendation statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while getting recommendation statistics",
        )


@router.get(
    "/programs/{program_id}/similar",
    response_model=List[dict],
    summary="Get similar programs",
    description="Get programs similar to a specific program",
)
async def get_similar_programs(
    program_id: int,
    limit: int = Query(
        5, ge=1, le=20, description="Maximum number of similar programs"
    ),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
):
    """
    Get programs similar to a specific program.

    This endpoint finds programs with similar characteristics (field, level, etc.).
    This endpoint does not require authentication as it provides general program information.
    """
    try:
        similar_programs = recommendation_service.get_similar_programs(
            program_id=program_id, limit=limit
        )

        logger.info(
            f"Found {len(similar_programs)} similar programs for program {program_id}"
        )
        return similar_programs

    except Exception as e:
        logger.error(f"Error getting similar programs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while getting similar programs",
        )
