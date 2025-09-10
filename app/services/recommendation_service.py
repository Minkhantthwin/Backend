from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models import (
    User,
    Program,
    UserInterest,
    UserQualificationStatus,
    University,
    Region,
    UserTestScore,
    UserQualification,
    ProgramRequirement,
)
from app.services.qualification_service import QualificationService
from app.schemas import DegreeLevel
from app.util.log import get_logger
import logging
from datetime import datetime, timedelta

logger = get_logger(__name__)


class RecommendationService:
    """Service for generating program recommendations based on user interests, qualifications, and test scores"""

    def __init__(self, db: Session):
        self.db = db
        self.qualification_service = QualificationService(db)

    def get_comprehensive_recommendations(
        self,
        user_id: int,
        preferred_countries: Optional[List[str]] = None,
        preferred_fields: Optional[List[str]] = None,
        degree_level: Optional[str] = None,
        max_tuition_fee: Optional[float] = None,
        language_preference: Optional[str] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Get comprehensive program recommendations based on user interests, qualifications, and test scores
        """
        try:
            # Get user to verify existence
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"error": "User not found", "user_id": user_id}

            # Refresh qualification statuses for active programs
            self._refresh_user_qualification_statuses(user_id)

            # Get recommendations from multiple sources
            interest_recommendations = self._get_interest_based_recommendations(
                user_id, preferred_fields, degree_level, limit * 2
            )

            qualification_recommendations = (
                self._get_qualification_based_recommendations(user_id, limit * 2)
            )

            test_score_recommendations = self._get_test_score_based_recommendations(
                user_id, degree_level, limit * 2
            )

            # Combine and score recommendations
            combined_recommendations = self._combine_and_score_recommendations(
                interest_recommendations,
                qualification_recommendations,
                test_score_recommendations,
                preferred_countries,
                max_tuition_fee,
                language_preference,
            )

            # Limit and format final results
            final_recommendations = combined_recommendations[:limit]

            return {
                "user_id": user_id,
                "recommendations": final_recommendations,
                "total_recommendations": len(final_recommendations),
                "recommendation_sources": {
                    "interest_based": len(interest_recommendations),
                    "qualification_based": len(qualification_recommendations),
                    "test_score_based": len(test_score_recommendations),
                },
                "filters_applied": {
                    "preferred_countries": preferred_countries or [],
                    "preferred_fields": preferred_fields or [],
                    "degree_level": degree_level,
                    "max_tuition_fee": max_tuition_fee,
                    "language_preference": language_preference,
                },
            }

        except Exception as e:
            logger.error(
                f"Error generating comprehensive recommendations for user {user_id}: {e}"
            )
            raise

    def _refresh_user_qualification_statuses(self, user_id: int, ttl_minutes: int = 60):
        """Refresh qualification statuses that are stale or missing."""
        try:
            cutoff = datetime.utcnow() - timedelta(minutes=ttl_minutes)

            # Get existing statuses
            existing_statuses = {
                s.program_id: s
                for s in self.db.query(UserQualificationStatus)
                .filter(UserQualificationStatus.user_id == user_id)
                .all()
            }

            # Get active programs
            active_programs = (
                self.db.query(Program).filter(Program.is_active == True).limit(50).all()
            )

            refreshed = 0
            for prog in active_programs:
                s = existing_statuses.get(prog.id)
                if (not s) or (s.last_checked is None) or (s.last_checked < cutoff):
                    try:
                        self.qualification_service.check_user_qualification(
                            user_id, prog.id
                        )
                        refreshed += 1
                    except Exception as inner:
                        logger.warning(
                            f"Qualification refresh failed user={user_id} program={prog.id}: {inner}"
                        )

            if refreshed:
                logger.info(
                    f"Qualification statuses refreshed for user {user_id}: {refreshed} programs"
                )
        except Exception as e:
            logger.warning(
                f"Qualification status refresh encountered an error for user {user_id}: {e}"
            )

    def _get_interest_based_recommendations(
        self,
        user_id: int,
        preferred_fields: Optional[List[str]] = None,
        degree_level: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get recommendations based on user interests"""
        try:
            # Get user interests
            user_interests = (
                self.db.query(UserInterest)
                .filter(UserInterest.user_id == user_id)
                .all()
            )

            if not user_interests:
                return []

            # Build query for programs matching interests
            query = self.db.query(Program).join(University).join(Region)

            # Filter by user interest fields
            interest_fields = [interest.field_of_study for interest in user_interests]
            if preferred_fields:
                interest_fields.extend(preferred_fields)

            query = query.filter(Program.field_of_study.in_(interest_fields))

            # Apply additional filters
            if degree_level:
                query = query.filter(Program.degree_level == degree_level)

            query = query.filter(Program.is_active == True)
            programs = query.limit(limit).all()

            recommendations = []
            for program in programs:
                # Calculate interest match score
                match_score = self._calculate_interest_match_score(
                    user_interests, program, preferred_fields
                )

                recommendations.append(
                    {
                        "program_id": program.id,
                        "program_name": program.name,
                        "university_name": program.university.name,
                        "country": program.university.region.name,
                        "field_of_study": program.field_of_study,
                        "degree_level": program.degree_level.value,
                        "tuition_fee": (
                            float(program.tuition_fee) if program.tuition_fee else None
                        ),
                        "currency": program.currency,
                        "language": program.language,
                        "match_score": match_score,
                        "recommendation_type": "interest_based",
                        "matching_factors": self._get_interest_matching_factors(
                            user_interests, program
                        ),
                        "recommendation_reasons": [
                            f"Matches your interest in {program.field_of_study}"
                        ],
                    }
                )

            return sorted(recommendations, key=lambda x: x["match_score"], reverse=True)

        except Exception as e:
            logger.error(f"Error getting interest-based recommendations: {e}")
            return []

    def _get_qualification_based_recommendations(
        self, user_id: int, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get recommendations based on user qualification status"""
        try:
            # Get qualification statuses from database
            qualification_statuses = (
                self.db.query(UserQualificationStatus)
                .join(Program)
                .join(University)
                .join(Region)
                .filter(UserQualificationStatus.user_id == user_id)
                .filter(
                    (UserQualificationStatus.is_qualified == True)
                    | (UserQualificationStatus.qualification_score >= 75)
                )
                .order_by(UserQualificationStatus.qualification_score.desc())
                .limit(limit)
                .all()
            )

            recommendations = []
            for status in qualification_statuses:
                program = status.program

                recommendations.append(
                    {
                        "program_id": program.id,
                        "program_name": program.name,
                        "university_name": program.university.name,
                        "country": program.university.region.name,
                        "field_of_study": program.field_of_study,
                        "degree_level": program.degree_level.value,
                        "tuition_fee": (
                            float(program.tuition_fee) if program.tuition_fee else None
                        ),
                        "currency": program.currency,
                        "language": program.language,
                        "match_score": float(status.qualification_score),
                        "recommendation_type": "qualification_based",
                        "qualification_status": (
                            "qualified" if status.is_qualified else "high_match"
                        ),
                        "requirements_met": status.missing_requirements,
                        "matching_factors": ["High qualification match"],
                        "recommendation_reasons": [
                            f"You {'meet all requirements' if status.is_qualified else 'have a high qualification match'} for this program",
                            f"Qualification score: {status.qualification_score}",
                        ],
                    }
                )

            return recommendations

        except Exception as e:
            logger.error(f"Error getting qualification-based recommendations: {e}")
            return []

    def _get_test_score_based_recommendations(
        self, user_id: int, degree_level: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get recommendations based on user test scores"""
        try:
            # Get user's valid test scores
            user_test_scores = (
                self.db.query(UserTestScore)
                .filter(UserTestScore.user_id == user_id)
                .all()
            )

            if not user_test_scores:
                return []

            # Get programs with requirements that match user's test scores
            query = self.db.query(Program).join(University).join(Region)

            if degree_level:
                query = query.filter(Program.degree_level == degree_level)

            query = query.filter(Program.is_active == True)
            programs = query.limit(limit * 3).all()  # Get more to filter

            recommendations = []
            for program in programs:
                score = self._calculate_test_score_match(user_test_scores, program)
                if score > 50:  # Only include if decent match
                    recommendations.append(
                        {
                            "program_id": program.id,
                            "program_name": program.name,
                            "university_name": program.university.name,
                            "country": program.university.region.name,
                            "field_of_study": program.field_of_study,
                            "degree_level": program.degree_level.value,
                            "tuition_fee": (
                                float(program.tuition_fee)
                                if program.tuition_fee
                                else None
                            ),
                            "currency": program.currency,
                            "language": program.language,
                            "match_score": score,
                            "recommendation_type": "test_score_based",
                            "matching_factors": ["Test score compatibility"],
                            "recommendation_reasons": [
                                "Your test scores are competitive for this program"
                            ],
                        }
                    )

            return sorted(
                recommendations, key=lambda x: x["match_score"], reverse=True
            )[:limit]

        except Exception as e:
            logger.error(f"Error getting test score based recommendations: {e}")
            return []

    def _calculate_test_score_match(
        self, user_test_scores: List[UserTestScore], program: Program
    ) -> float:
        """Calculate how well user's test scores match program requirements"""
        try:
            # Get program requirements
            requirements = (
                self.db.query(ProgramRequirement)
                .filter(ProgramRequirement.program_id == program.id)
                .filter(
                    ProgramRequirement.requirement_type.in_(["test_score", "language"])
                )
                .all()
            )

            if not requirements:
                return 60.0  # Base score if no test requirements

            total_score = 0
            matched_requirements = 0

            for req in requirements:
                test_type = req.test_type or self._extract_test_type_from_description(
                    req.description
                )
                required_score = self._parse_requirement_value(req.requirement_value)

                if test_type and required_score:
                    user_score = self._get_best_user_score(user_test_scores, test_type)
                    if user_score:
                        if user_score >= required_score:
                            total_score += 100
                        else:
                            # Partial score based on how close they are
                            ratio = user_score / required_score
                            total_score += min(ratio * 100, 95)
                        matched_requirements += 1

            if matched_requirements == 0:
                return 60.0  # Base score if no matching test types

            return total_score / matched_requirements

        except Exception as e:
            logger.error(f"Error calculating test score match: {e}")
            return 50.0

    def get_similar_programs(
        self, program_id: int, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get programs similar to a given program"""
        try:
            # Get the base program
            base_program = (
                self.db.query(Program)
                .join(University)
                .join(Region)
                .filter(Program.id == program_id)
                .first()
            )

            if not base_program:
                return []

            # Find similar programs
            similar_programs = (
                self.db.query(Program)
                .join(University)
                .join(Region)
                .filter(Program.id != program_id)
                .filter(Program.is_active == True)
                .filter(
                    (Program.field_of_study == base_program.field_of_study)
                    | (Program.degree_level == base_program.degree_level)
                )
                .limit(limit)
                .all()
            )

            recommendations = []
            for program in similar_programs:
                similarity_score = self._calculate_program_similarity(
                    base_program, program
                )

                recommendations.append(
                    {
                        "program_id": program.id,
                        "program_name": program.name,
                        "university_name": program.university.name,
                        "country": program.university.region.name,
                        "field_of_study": program.field_of_study,
                        "degree_level": program.degree_level.value,
                        "tuition_fee": (
                            float(program.tuition_fee) if program.tuition_fee else None
                        ),
                        "currency": program.currency,
                        "language": program.language,
                        "similarity_score": similarity_score,
                        "recommendation_type": "similar_program",
                        "matching_factors": self._get_similarity_factors(
                            base_program, program
                        ),
                        "recommendation_reasons": [f"Similar to {base_program.name}"],
                    }
                )

            return sorted(
                recommendations, key=lambda x: x["similarity_score"], reverse=True
            )

        except Exception as e:
            logger.error(
                f"Error getting similar programs for program {program_id}: {e}"
            )
            return []

    def get_similar_programs_by_field(
        self, field_of_study: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get programs similar to a specific field of study"""
        try:
            # Find programs in the same or related fields
            similar_programs = (
                self.db.query(Program)
                .join(University)
                .join(Region)
                .filter(Program.is_active == True)
                .filter(
                    (Program.field_of_study.ilike(f"%{field_of_study}%"))
                    | (Program.field_of_study.ilike(f"%{field_of_study.split()[0]}%"))
                )
                .limit(limit)
                .all()
            )

            recommendations = []
            for program in similar_programs:
                # Calculate similarity score based on field match
                if program.field_of_study.lower() == field_of_study.lower():
                    similarity_score = 100.0
                elif field_of_study.lower() in program.field_of_study.lower():
                    similarity_score = 80.0
                elif any(
                    word in program.field_of_study.lower()
                    for word in field_of_study.lower().split()
                ):
                    similarity_score = 60.0
                else:
                    similarity_score = 40.0

                recommendations.append(
                    {
                        "program_id": program.id,
                        "program_name": program.name,
                        "university_name": program.university.name,
                        "country": program.university.region.name,
                        "field_of_study": program.field_of_study,
                        "degree_level": program.degree_level.value,
                        "tuition_fee": (
                            float(program.tuition_fee) if program.tuition_fee else None
                        ),
                        "currency": program.currency,
                        "language": program.language,
                        "similarity_score": similarity_score,
                        "recommendation_type": "field_similar",
                        "matching_factors": [f"Similar field to {field_of_study}"],
                        "recommendation_reasons": [f"Related to {field_of_study}"],
                    }
                )

            return sorted(
                recommendations, key=lambda x: x["similarity_score"], reverse=True
            )

        except Exception as e:
            logger.error(
                f"Error getting similar programs for field {field_of_study}: {e}"
            )
            return []

    def _calculate_program_similarity(
        self, program1: Program, program2: Program
    ) -> float:
        """Calculate similarity score between two programs"""
        score = 0.0

        # Field of study match (highest weight)
        if program1.field_of_study == program2.field_of_study:
            score += 40
        elif (
            program1.field_of_study in program2.field_of_study
            or program2.field_of_study in program1.field_of_study
        ):
            score += 20

        # Degree level match
        if program1.degree_level == program2.degree_level:
            score += 30

        # Language match
        if program1.language == program2.language:
            score += 15

        # Duration match
        if program1.duration_years == program2.duration_years:
            score += 10

        # University ranking proximity (if available)
        if program1.university.ranking_world and program2.university.ranking_world:
            rank_diff = abs(
                program1.university.ranking_world - program2.university.ranking_world
            )
            if rank_diff < 50:
                score += 5

        return min(score, 100.0)

    def _get_similarity_factors(
        self, program1: Program, program2: Program
    ) -> List[str]:
        """Get factors that make programs similar"""
        factors = []

        if program1.field_of_study == program2.field_of_study:
            factors.append(f"Same field of study: {program1.field_of_study}")

        if program1.degree_level == program2.degree_level:
            factors.append(f"Same degree level: {program1.degree_level.value}")

        if program1.language == program2.language:
            factors.append(f"Same language: {program1.language}")

        if program1.duration_years == program2.duration_years:
            factors.append(f"Same duration: {program1.duration_years} years")

        return factors

    def _extract_test_type_from_description(self, description: str) -> Optional[str]:
        """Extract test type from requirement description"""
        if not description:
            return None

        test_types = ["IELTS", "TOEFL", "GRE", "GMAT", "SAT", "ACT", "PTE"]
        description_upper = description.upper()

        for test in test_types:
            if test in description_upper:
                return test
        return None

    def _parse_requirement_value(self, value: str) -> Optional[float]:
        """Parse requirement value to float"""
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _get_best_user_score(
        self, user_test_scores: List[UserTestScore], test_type: str
    ) -> Optional[float]:
        """Get user's best score for a specific test type"""
        matching_scores = [
            score
            for score in user_test_scores
            if score.test_type.upper() == test_type.upper()
        ]

        if not matching_scores:
            return None

        try:
            return max(float(score.score) for score in matching_scores)
        except (ValueError, TypeError):
            return None

    def _combine_and_score_recommendations(
        self,
        interest_recommendations: List[Dict[str, Any]],
        qualification_recommendations: List[Dict[str, Any]],
        test_score_recommendations: List[Dict[str, Any]],
        preferred_countries: Optional[List[str]] = None,
        max_tuition_fee: Optional[float] = None,
        language_preference: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Combine recommendations from different sources and apply additional scoring"""

        # Combine all recommendations
        all_recommendations = {}

        # Process each source with different weights
        for rec in interest_recommendations:
            program_id = rec["program_id"]
            rec["final_score"] = rec["match_score"] * 0.4  # 40% weight for interests
            all_recommendations[program_id] = rec

        for rec in qualification_recommendations:
            program_id = rec["program_id"]
            if program_id in all_recommendations:
                # Boost score if program appears in multiple sources
                all_recommendations[program_id]["final_score"] += (
                    rec["match_score"] * 0.5
                )  # 50% weight
                all_recommendations[program_id]["matching_factors"].extend(
                    rec["matching_factors"]
                )
                all_recommendations[program_id]["recommendation_reasons"].extend(
                    rec["recommendation_reasons"]
                )
                all_recommendations[program_id]["recommendation_type"] = "multi_source"
            else:
                rec["final_score"] = rec["match_score"] * 0.5
                all_recommendations[program_id] = rec

        for rec in test_score_recommendations:
            program_id = rec["program_id"]
            if program_id in all_recommendations:
                all_recommendations[program_id]["final_score"] += (
                    rec["match_score"] * 0.3
                )  # 30% weight
                all_recommendations[program_id]["matching_factors"].extend(
                    rec["matching_factors"]
                )
                all_recommendations[program_id]["recommendation_reasons"].extend(
                    rec["recommendation_reasons"]
                )
                all_recommendations[program_id]["recommendation_type"] = "multi_source"
            else:
                rec["final_score"] = rec["match_score"] * 0.3
                all_recommendations[program_id] = rec

        # Apply additional filters and scoring
        filtered_recommendations = []
        for rec in all_recommendations.values():
            # Apply country filter
            if preferred_countries and rec["country"] not in preferred_countries:
                rec["final_score"] *= 0.7  # Reduce score but don't eliminate
            elif preferred_countries and rec["country"] in preferred_countries:
                rec["final_score"] *= 1.2  # Boost score for preferred countries

            # Apply tuition fee filter
            if (
                max_tuition_fee
                and rec["tuition_fee"]
                and rec["tuition_fee"] > max_tuition_fee
            ):
                rec[
                    "final_score"
                ] *= 0.5  # Significantly reduce score for expensive programs

            # Apply language preference
            if language_preference and rec["language"] == language_preference:
                rec["final_score"] *= 1.1  # Small boost for language match

            # Clean up duplicate factors and reasons
            rec["matching_factors"] = list(set(rec["matching_factors"]))
            rec["recommendation_reasons"] = list(set(rec["recommendation_reasons"]))

            filtered_recommendations.append(rec)

        # Sort by final score
        return sorted(
            filtered_recommendations, key=lambda x: x["final_score"], reverse=True
        )

    def _calculate_interest_match_score(
        self,
        user_interests: List[UserInterest],
        program: Program,
        preferred_fields: Optional[List[str]] = None,
    ) -> float:
        """Calculate match score based on user interests"""
        score = 0.0

        # Check direct field match
        for interest in user_interests:
            if interest.field_of_study.lower() == program.field_of_study.lower():
                # Weight by interest level
                if interest.interest_level == "high":
                    score += 90
                elif interest.interest_level == "medium":
                    score += 70
                else:  # low
                    score += 50
                break

        # Check partial field match
        if score == 0:
            for interest in user_interests:
                if (
                    interest.field_of_study.lower() in program.field_of_study.lower()
                    or program.field_of_study.lower() in interest.field_of_study.lower()
                ):
                    if interest.interest_level == "high":
                        score += 60
                    elif interest.interest_level == "medium":
                        score += 40
                    else:  # low
                        score += 25
                    break

        # Check preferred fields
        if preferred_fields:
            for field in preferred_fields:
                if field.lower() == program.field_of_study.lower():
                    score += 20
                    break
                elif (
                    field.lower() in program.field_of_study.lower()
                    or program.field_of_study.lower() in field.lower()
                ):
                    score += 10
                    break

        return min(score, 100.0)  # Cap at 100

    def _get_interest_matching_factors(
        self, user_interests: List[UserInterest], program: Program
    ) -> List[str]:
        """Get matching factors for interest-based recommendations"""
        factors = []

        for interest in user_interests:
            if interest.field_of_study.lower() == program.field_of_study.lower():
                factors.append(
                    f"Direct match with your {interest.interest_level} interest in {interest.field_of_study}"
                )
            elif (
                interest.field_of_study.lower() in program.field_of_study.lower()
                or program.field_of_study.lower() in interest.field_of_study.lower()
            ):
                factors.append(f"Related to your interest in {interest.field_of_study}")

        if not factors:
            factors.append("General field match")

        return factors

    def get_similar_programs(
        self, program_id: int, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get programs similar to a given program"""
        try:
            # Get the base program
            base_program = (
                self.db.query(Program)
                .join(University)
                .join(Region)
                .filter(Program.id == program_id)
                .first()
            )

            if not base_program:
                return []

            # Find similar programs
            similar_programs = (
                self.db.query(Program)
                .join(University)
                .join(Region)
                .filter(Program.id != program_id)
                .filter(Program.is_active == True)
                .filter(
                    (Program.field_of_study == base_program.field_of_study)
                    | (Program.degree_level == base_program.degree_level)
                )
                .limit(limit)
                .all()
            )

            recommendations = []
            for program in similar_programs:
                similarity_score = self._calculate_program_similarity(
                    base_program, program
                )

                recommendations.append(
                    {
                        "program_id": program.id,
                        "program_name": program.name,
                        "university_name": program.university.name,
                        "country": program.university.region.name,
                        "field_of_study": program.field_of_study,
                        "degree_level": program.degree_level.value,
                        "tuition_fee": (
                            float(program.tuition_fee) if program.tuition_fee else None
                        ),
                        "currency": program.currency,
                        "language": program.language,
                        "similarity_score": similarity_score,
                        "recommendation_type": "similar_program",
                        "matching_factors": self._get_similarity_factors(
                            base_program, program
                        ),
                        "recommendation_reasons": [f"Similar to {base_program.name}"],
                    }
                )

            return sorted(
                recommendations, key=lambda x: x["similarity_score"], reverse=True
            )

        except Exception as e:
            logger.error(
                f"Error getting similar programs for program {program_id}: {e}"
            )
            return []

    def get_similar_programs_by_field(
        self, field_of_study: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get programs similar to a specific field of study"""
        try:
            # Find programs in the same or related fields
            similar_programs = (
                self.db.query(Program)
                .join(University)
                .join(Region)
                .filter(Program.is_active == True)
                .filter(
                    (Program.field_of_study.ilike(f"%{field_of_study}%"))
                    | (Program.field_of_study.ilike(f"%{field_of_study.split()[0]}%"))
                )
                .limit(limit)
                .all()
            )

            recommendations = []
            for program in similar_programs:
                # Calculate similarity score based on field match
                if program.field_of_study.lower() == field_of_study.lower():
                    similarity_score = 100.0
                elif field_of_study.lower() in program.field_of_study.lower():
                    similarity_score = 80.0
                elif any(
                    word in program.field_of_study.lower()
                    for word in field_of_study.lower().split()
                ):
                    similarity_score = 60.0
                else:
                    similarity_score = 40.0

                recommendations.append(
                    {
                        "program_id": program.id,
                        "program_name": program.name,
                        "university_name": program.university.name,
                        "country": program.university.region.name,
                        "field_of_study": program.field_of_study,
                        "degree_level": program.degree_level.value,
                        "tuition_fee": (
                            float(program.tuition_fee) if program.tuition_fee else None
                        ),
                        "currency": program.currency,
                        "language": program.language,
                        "similarity_score": similarity_score,
                        "recommendation_type": "field_similar",
                        "matching_factors": [f"Similar field to {field_of_study}"],
                        "recommendation_reasons": [f"Related to {field_of_study}"],
                    }
                )

            return sorted(
                recommendations, key=lambda x: x["similarity_score"], reverse=True
            )

        except Exception as e:
            logger.error(
                f"Error getting similar programs for field {field_of_study}: {e}"
            )
            return []

    def _calculate_program_similarity(
        self, program1: Program, program2: Program
    ) -> float:
        """Calculate similarity score between two programs"""
        score = 0.0

        # Field of study match (highest weight)
        if program1.field_of_study == program2.field_of_study:
            score += 40
        elif (
            program1.field_of_study in program2.field_of_study
            or program2.field_of_study in program1.field_of_study
        ):
            score += 20

        # Degree level match
        if program1.degree_level == program2.degree_level:
            score += 30

        # Language match
        if program1.language == program2.language:
            score += 15

        # Duration match
        if program1.duration_years == program2.duration_years:
            score += 10

        # University ranking proximity (if available)
        if program1.university.ranking_world and program2.university.ranking_world:
            rank_diff = abs(
                program1.university.ranking_world - program2.university.ranking_world
            )
            if rank_diff < 50:
                score += 5

        return min(score, 100.0)

    def _get_similarity_factors(
        self, program1: Program, program2: Program
    ) -> List[str]:
        """Get factors that make programs similar"""
        factors = []

        if program1.field_of_study == program2.field_of_study:
            factors.append(f"Same field of study: {program1.field_of_study}")

        if program1.degree_level == program2.degree_level:
            factors.append(f"Same degree level: {program1.degree_level.value}")

        if program1.language == program2.language:
            factors.append(f"Same language: {program1.language}")

        if program1.duration_years == program2.duration_years:
            factors.append(f"Same duration: {program1.duration_years} years")

        return factors
