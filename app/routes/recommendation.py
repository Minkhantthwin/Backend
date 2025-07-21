from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_mysql_session
from app.services.recommendation_service import RecommendationService
from app.schemas import RecommendationRequest, RecommendationListResponse, DegreeLevel
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
    description="Get program recommendations based on user interests, qualification status, and preferences",
)
async def get_user_recommendations(
    user_id: int,
    preferred_countries: Optional[List[str]] = Query(
        None, description="List of preferred countries"
    ),
    preferred_fields: Optional[List[str]] = Query(
        None, description="List of preferred fields of study"
    ),
    degree_level: Optional[str] = Query(None, description="Preferred degree level"),
    max_tuition_fee: Optional[float] = Query(None, description="Maximum tuition fee"),
    language_preference: Optional[str] = Query(
        None, description="Preferred language of instruction"
    ),
    limit: int = Query(
        10, ge=1, le=50, description="Maximum number of recommendations"
    ),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
):
    """
    Get comprehensive program recommendations for a user.

    This endpoint combines multiple recommendation sources:
    - Interest-based recommendations from user preferences
    - Qualification-based recommendations from assessment results
    - Graph-based recommendations from Neo4j relationships

    **Parameters:**
    - **user_id**: ID of the user to get recommendations for
    - **preferred_countries**: Filter by preferred countries
    - **preferred_fields**: Additional fields of study to consider
    - **degree_level**: Filter by degree level (bachelor, master, phd, etc.)
    - **max_tuition_fee**: Maximum acceptable tuition fee
    - **language_preference**: Preferred language of instruction
    - **limit**: Maximum number of recommendations to return
    """
    try:
        recommendations = recommendation_service.get_comprehensive_recommendations(
            user_id=user_id,
            preferred_countries=preferred_countries,
            preferred_fields=preferred_fields,
            degree_level=degree_level,
            max_tuition_fee=max_tuition_fee,
            language_preference=language_preference,
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
    "/users/{user_id}/recommendations/interest-based",
    response_model=List[dict],
    summary="Get interest-based recommendations",
    description="Get program recommendations based only on user interests",
)
async def get_interest_based_recommendations(
    user_id: int,
    preferred_fields: Optional[List[str]] = Query(
        None, description="Additional fields to consider"
    ),
    degree_level: Optional[str] = Query(None, description="Filter by degree level"),
    limit: int = Query(
        10, ge=1, le=50, description="Maximum number of recommendations"
    ),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
):
    """
    Get program recommendations based only on user interests.

    This endpoint focuses specifically on matching programs to user's declared interests.
    """
    try:
        recommendations = recommendation_service._get_interest_based_recommendations(
            user_id=user_id,
            preferred_fields=preferred_fields,
            degree_level=degree_level,
            limit=limit,
        )

        logger.info(
            f"Generated {len(recommendations)} interest-based recommendations for user {user_id}"
        )
        return recommendations

    except Exception as e:
        logger.error(f"Error getting interest-based recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while getting interest-based recommendations",
        )


@router.get(
    "/users/{user_id}/recommendations/qualification-based",
    response_model=List[dict],
    summary="Get qualification-based recommendations",
    description="Get program recommendations based only on user qualification status",
)
async def get_qualification_based_recommendations(
    user_id: int,
    limit: int = Query(
        10, ge=1, le=50, description="Maximum number of recommendations"
    ),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
):
    """
    Get program recommendations based only on user qualification status.

    This endpoint focuses specifically on programs where the user meets requirements.
    """
    try:
        recommendations = (
            recommendation_service._get_qualification_based_recommendations(
                user_id=user_id, limit=limit
            )
        )

        logger.info(
            f"Generated {len(recommendations)} qualification-based recommendations for user {user_id}"
        )
        return recommendations

    except Exception as e:
        logger.error(f"Error getting qualification-based recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while getting qualification-based recommendations",
        )


@router.get(
    "/users/{user_id}/recommendations/neo4j-graph",
    response_model=List[dict],
    summary="Get Neo4j graph-based recommendations",
    description="Get program recommendations based on Neo4j graph relationships",
)
async def get_neo4j_recommendations(
    user_id: int,
    limit: int = Query(
        10, ge=1, le=50, description="Maximum number of recommendations"
    ),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
):
    """
    Get program recommendations based on Neo4j graph relationships.

    This endpoint leverages graph database relationships for recommendations.
    """
    try:
        recommendations = recommendation_service._get_neo4j_recommendations(
            user_id=user_id, limit=limit
        )

        logger.info(
            f"Generated {len(recommendations)} Neo4j-based recommendations for user {user_id}"
        )
        return recommendations

    except Exception as e:
        logger.error(f"Error getting Neo4j recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while getting Neo4j recommendations",
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


@router.post(
    "/recommendations/custom",
    response_model=dict,
    summary="Get custom recommendations",
    description="Get recommendations with custom parameters",
)
async def get_custom_recommendations(
    request: RecommendationRequest,
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
):
    """
    Get custom program recommendations based on specific request parameters.

    This endpoint allows for detailed customization of recommendation parameters.
    """
    try:
        recommendations = recommendation_service.get_comprehensive_recommendations(
            user_id=request.user_id,
            preferred_countries=request.preferred_countries,
            preferred_fields=request.preferred_fields,
            degree_level=request.degree_level.value if request.degree_level else None,
            max_tuition_fee=request.max_tuition_fee,
            language_preference=request.language_preference,
            limit=10,
        )

        if "error" in recommendations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=recommendations["error"]
            )

        logger.info(f"Generated custom recommendations for user {request.user_id}")
        return recommendations

    except ValueError as e:
        logger.warning(f"Invalid custom recommendation request: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting custom recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while getting custom recommendations",
        )


@router.get(
    "/recommendations/stats/{user_id}",
    response_model=dict,
    summary="Get recommendation statistics",
    description="Get statistics about available recommendations for a user",
)
async def get_recommendation_stats(
    user_id: int,
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
):
    """
    Get statistics about available recommendations for a user.

    This endpoint provides insights into recommendation sources and coverage.
    """
    try:
        # Get basic counts from each recommendation source
        interest_recs = recommendation_service._get_interest_based_recommendations(
            user_id, limit=100
        )
        qualification_recs = (
            recommendation_service._get_qualification_based_recommendations(
                user_id, limit=100
            )
        )
        neo4j_recs = recommendation_service._get_neo4j_recommendations(
            user_id, limit=100
        )

        stats = {
            "user_id": user_id,
            "recommendation_sources": {
                "interest_based_count": len(interest_recs),
                "qualification_based_count": len(qualification_recs),
                "neo4j_graph_count": len(neo4j_recs),
            },
            "total_unique_programs": len(
                set(
                    [r["program_id"] for r in interest_recs]
                    + [r["program_id"] for r in qualification_recs]
                    + [r["program_id"] for r in neo4j_recs]
                )
            ),
            "top_countries": list(
                set(
                    [
                        r["country"]
                        for r in interest_recs + qualification_recs + neo4j_recs
                    ]
                )
            )[:10],
            "top_fields": list(
                set(
                    [
                        r["field_of_study"]
                        for r in interest_recs + qualification_recs + neo4j_recs
                    ]
                )
            )[:10],
            "degree_levels": list(
                set(
                    [
                        r["degree_level"]
                        for r in interest_recs + qualification_recs + neo4j_recs
                    ]
                )
            ),
        }

        logger.info(f"Generated recommendation statistics for user {user_id}")
        return stats

    except Exception as e:
        logger.error(f"Error getting recommendation statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while getting recommendation statistics",
        )
