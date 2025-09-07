from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from app.models import (
    User,
    Program,
    UserTestScore,
    UserQualification,
    ProgramRequirement,
    UserQualificationStatus,
)
from app.schemas import QualificationCheckResponse, QualificationSummaryResponse
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


class QualificationService:
    """Service for checking user qualifications against program requirements"""

    def __init__(self, db: Session):
        self.db = db

    def check_user_qualification(self, user_id: int, program_id: int) -> Dict:
        """Check if user meets all requirements for a specific program"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            program = self.db.query(Program).filter(Program.id == program_id).first()

            if not user or not program:
                return {"error": "User or program not found"}

            # Get program requirements
            requirements = (
                self.db.query(ProgramRequirement)
                .filter(ProgramRequirement.program_id == program_id)
                .all()
            )

            # Get user test scores and qualifications
            test_scores = (
                self.db.query(UserTestScore)
                .filter(UserTestScore.user_id == user_id)
                .all()
            )

            qualifications = (
                self.db.query(UserQualification)
                .filter(UserQualification.user_id == user_id)
                .all()
            )

            # Check each requirement
            qualification_results = []
            met_requirements = 0
            total_requirements = len(requirements)
            missing_requirements = []

            for req in requirements:
                result = self._check_single_requirement(
                    req, test_scores, qualifications
                )
                qualification_results.append(result)

                if result["is_met"]:
                    met_requirements += 1
                else:
                    missing_requirements.append(result)

            # Calculate qualification score
            qualification_score = (
                (met_requirements / total_requirements * 100)
                if total_requirements > 0
                else 0
            )
            is_qualified = (
                qualification_score >= 100
            )  # Must meet all mandatory requirements

            # Check for mandatory requirements
            mandatory_unmet = any(
                not result["is_met"]
                for result in qualification_results
                if result["is_mandatory"]
            )

            if mandatory_unmet:
                is_qualified = False

            # Save or update qualification status
            self._save_qualification_status(
                user_id,
                program_id,
                is_qualified,
                qualification_score,
                missing_requirements,
                met_requirements,
                total_requirements,
            )

            return {
                "user_id": user_id,
                "program_id": program_id,
                "program_name": program.name,
                "university_name": program.university.name,
                "is_qualified": is_qualified,
                "qualification_score": qualification_score,
                "requirements_met": met_requirements,
                "total_requirements": total_requirements,
                "missing_requirements": missing_requirements,
                "detailed_results": qualification_results,
                "checked_at": datetime.utcnow(),
            }

        except Exception as e:
            logger.error(
                f"Error checking qualification for user {user_id}, program {program_id}: {e}"
            )
            raise

    def _check_single_requirement(
        self,
        requirement: ProgramRequirement,
        test_scores: List[UserTestScore],
        qualifications: List[UserQualification],
    ) -> Dict:
        """Check if user meets a single requirement"""

        result = {
            "requirement_id": requirement.id,
            "requirement_type": requirement.requirement_type,
            "requirement_value": requirement.requirement_value,
            "is_mandatory": requirement.is_mandatory,
            "is_met": False,
            "user_value": None,
            "details": "",
        }

        if requirement.requirement_type == "test_score":
            result.update(self._check_test_score_requirement(requirement, test_scores))
        elif requirement.requirement_type == "gpa":
            result.update(self._check_gpa_requirement(requirement, qualifications))
        elif requirement.requirement_type == "degree_level":
            result.update(self._check_degree_requirement(requirement, qualifications))
        elif requirement.requirement_type == "language":
            result.update(self._check_language_requirement(requirement, test_scores))

        return result

    def _check_test_score_requirement(
        self, requirement: ProgramRequirement, test_scores: List[UserTestScore]
    ) -> Dict:
        """Check test score requirements (IELTS, TOEFL, GRE, etc.)"""

        required_score = float(requirement.requirement_value)
        test_type = requirement.test_type or self._extract_test_type(
            requirement.description
        )

        # Find matching test scores
        matching_scores = [
            score
            for score in test_scores
            if score.test_type.upper() == test_type.upper()
        ]

        if not matching_scores:
            return {
                "is_met": False,
                "user_value": None,
                "details": f"No {test_type} score found",
            }

        # Get the most recent valid score
        valid_scores = [
            score
            for score in matching_scores
            if not score.expiry_date or score.expiry_date > date.today()
        ]

        if not valid_scores:
            return {
                "is_met": False,
                "user_value": None,
                "details": f"All {test_type} scores have expired",
            }

        # Get highest score
        best_score = max(valid_scores, key=lambda x: float(x.score))
        user_score = float(best_score.score)

        return {
            "is_met": user_score >= required_score,
            "user_value": user_score,
            "details": f"{test_type}: {user_score} (required: {required_score})",
        }

    def _check_gpa_requirement(
        self, requirement: ProgramRequirement, qualifications: List[UserQualification]
    ) -> Dict:
        """Check GPA requirements"""

        required_gpa = float(requirement.requirement_value)

        # Find highest GPA from completed degrees
        completed_qualifications = [
            qual for qual in qualifications if qual.is_completed and qual.grade_point
        ]

        if not completed_qualifications:
            return {
                "is_met": False,
                "user_value": None,
                "details": "No completed qualifications with GPA found",
            }

        # Convert GPAs to 4.0 scale for comparison
        highest_gpa = 0.0
        best_qualification = None

        for qual in completed_qualifications:
            try:
                gpa = float(qual.grade_point)
                max_gpa = float(qual.max_grade_point) if qual.max_grade_point else 4.0

                # Normalize to 4.0 scale
                normalized_gpa = (gpa / max_gpa) * 4.0

                if normalized_gpa > highest_gpa:
                    highest_gpa = normalized_gpa
                    best_qualification = qual

            except (ValueError, TypeError):
                continue

        return {
            "is_met": highest_gpa >= required_gpa,
            "user_value": highest_gpa,
            "details": f"GPA: {highest_gpa:.2f}/4.0 from {best_qualification.institution_name if best_qualification else 'N/A'} (required: {required_gpa})",
        }

    def _check_degree_requirement(
        self, requirement: ProgramRequirement, qualifications: List[UserQualification]
    ) -> Dict:
        """Check degree level requirements"""

        required_level = requirement.requirement_value.lower()

        # Define degree hierarchy
        degree_hierarchy = {
            "high_school": 1,
            "diploma": 2,
            "certificate": 2,
            "bachelor": 3,
            "master": 4,
            "phd": 5,
        }

        required_level_rank = degree_hierarchy.get(required_level, 0)

        # Find highest completed degree
        completed_qualifications = [
            qual for qual in qualifications if qual.is_completed
        ]

        if not completed_qualifications:
            return {
                "is_met": False,
                "user_value": None,
                "details": "No completed qualifications found",
            }

        highest_rank = 0
        highest_degree = None

        for qual in completed_qualifications:
            degree_rank = degree_hierarchy.get(qual.qualification_type.value, 0)
            if degree_rank > highest_rank:
                highest_rank = degree_rank
                highest_degree = qual

        return {
            "is_met": highest_rank >= required_level_rank,
            "user_value": (
                highest_degree.qualification_type.value if highest_degree else None
            ),
            "details": f"Highest degree: {highest_degree.qualification_type.value if highest_degree else 'None'} (required: {required_level})",
        }

    def _check_language_requirement(
        self, requirement: ProgramRequirement, test_scores: List[UserTestScore]
    ) -> Dict:
        """Check language proficiency requirements"""

        # This is similar to test score but specifically for language tests
        language_tests = ["IELTS", "TOEFL", "TOEIC", "PTE"]

        for test in language_tests:
            test_result = self._check_test_score_requirement(requirement, test_scores)
            if test_result["is_met"]:
                return test_result

        return {
            "is_met": False,
            "user_value": None,
            "details": "No valid language test scores found",
        }

    def _extract_test_type(self, description: str) -> str:
        """Extract test type from requirement description"""
        if not description:
            return ""

        test_types = ["IELTS", "TOEFL", "GRE", "GMAT", "SAT", "ACT", "GOV"]
        description_upper = description.upper()

        for test in test_types:
            if test in description_upper:
                return test

        return ""

    def _save_qualification_status(
        self,
        user_id: int,
        program_id: int,
        is_qualified: bool,
        qualification_score: float,
        missing_requirements: List[Dict],
        requirements_met: int = 0,
        total_requirements: int = 0,
    ):
        """Save or update qualification status in MySQL"""
        try:
            # Check if status already exists
            existing_status = (
                self.db.query(UserQualificationStatus)
                .filter(
                    UserQualificationStatus.user_id == user_id,
                    UserQualificationStatus.program_id == program_id,
                )
                .first()
            )

            checked_at = datetime.utcnow()

            if existing_status:
                existing_status.is_qualified = is_qualified
                existing_status.qualification_score = qualification_score
                existing_status.missing_requirements = missing_requirements
                existing_status.last_checked = checked_at
            else:
                status = UserQualificationStatus(
                    user_id=user_id,
                    program_id=program_id,
                    is_qualified=is_qualified,
                    qualification_score=qualification_score,
                    missing_requirements=missing_requirements,
                    last_checked=checked_at,
                )
                self.db.add(status)

            self.db.commit()
            logger.debug(f"Successfully updated qualification status for user {user_id}, program {program_id}")

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving qualification status: {e}")
            raise

    def get_user_qualifications_summary(self, user_id: int) -> Dict:
        """Get summary of user's qualifications for all programs"""
        try:
            # Get all qualification statuses for user
            statuses = (
                self.db.query(UserQualificationStatus)
                .filter(UserQualificationStatus.user_id == user_id)
                .all()
            )

            qualified_programs = []
            partially_qualified = []
            not_qualified = []

            for status in statuses:
                program_info = {
                    "program_id": status.program_id,
                    "program_name": status.program.name,
                    "university_name": status.program.university.name,
                    "qualification_score": status.qualification_score,
                    "missing_requirements": status.missing_requirements,
                    "last_checked": status.last_checked,
                }

                if status.is_qualified:
                    qualified_programs.append(program_info)
                elif status.qualification_score >= 75:
                    partially_qualified.append(program_info)
                else:
                    not_qualified.append(program_info)

            return {
                "user_id": user_id,
                "qualified_programs": qualified_programs,
                "partially_qualified": partially_qualified,
                "not_qualified": not_qualified,
                "total_programs_checked": len(statuses),
            }

        except Exception as e:
            logger.error(f"Error getting qualification summary for user {user_id}: {e}")
            raise

    def check_user_against_all_programs(self, user_id: int) -> List[Dict]:
        """Check user qualification against all active programs"""
        try:
            # Get all active programs
            programs = self.db.query(Program).filter(Program.is_active == True).all()

            results = []
            total_programs = len(programs)

            logger.info(f"Checking user {user_id} against {total_programs} active programs")

            for program in programs:
                try:
                    result = self.check_user_qualification(user_id, program.id)
                    results.append(result)
                    logger.debug(f"Updated qualification status for user {user_id}, program {program.id}")
                except Exception as e:
                    logger.error(
                        f"Error checking program {program.id} for user {user_id}: {e}"
                    )
                    continue

            logger.info(f"Completed qualification check for user {user_id}: {len(results)} programs checked")
            return results

        except Exception as e:
            logger.error(f"Error checking user {user_id} against all programs: {e}")
            raise

    def get_program_recommendations_by_qualification(
        self, user_id: int, limit: int = 10
    ) -> List[Dict]:
        """Get program recommendations based on qualification status"""
        try:
            # Get qualified and highly matched programs
            statuses = (
                self.db.query(UserQualificationStatus)
                .join(Program)
                .join(Program.university)
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
            for status in statuses:
                program = status.program
                recommendations.append({
                    "program_id": status.program_id,
                    "program_name": program.name,
                    "university_name": program.university.name if program.university else None,
                    "field_of_study": program.field_of_study,
                    "degree_level": program.degree_level.value,
                    "qualification_score": float(status.qualification_score),
                    "is_qualified": status.is_qualified,
                    "recommendation_reason": (
                        "You meet all requirements" if status.is_qualified 
                        else f"High qualification match ({status.qualification_score}%)"
                    ),
                    "checked_at": status.last_checked,
                })

            return recommendations

        except Exception as e:
            logger.error(f"Error getting program recommendations by qualification: {e}")
            return []
