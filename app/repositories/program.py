from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from app.models import Program, ProgramRequirement
from app.schemas import ProgramCreate
import logging

logger = logging.getLogger(__name__)


class ProgramRepository:
    """Repository for program database operations"""

    def __init__(self, db: Session):
        self.db = db

    def create_program(self, program_data: ProgramCreate) -> Program:
        """Create a new program with requirements"""
        try:
            # Create program object without requirements
            program_dict = program_data.model_dump(exclude={"requirements"})
            db_program = Program(**program_dict)
            self.db.add(db_program)
            self.db.flush()  # Get program ID without committing

            # Add requirements
            if program_data.requirements:
                for req_data in program_data.requirements:
                    requirement = ProgramRequirement(
                        program_id=db_program.id, **req_data.model_dump()
                    )
                    self.db.add(requirement)

            self.db.commit()
            self.db.refresh(db_program)

            logger.info(f"Program created successfully: {db_program.name}")
            return db_program

        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to create program due to integrity constraint: {e}")
            raise ValueError("Invalid university ID or duplicate program")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create program: {e}")
            raise

    def get_program_by_id(self, program_id: int) -> Optional[Program]:
        """Get program by ID with relationships"""
        try:
            program = self.db.query(Program).filter(Program.id == program_id).first()
            return program
        except Exception as e:
            logger.error(f"Failed to get program by ID {program_id}: {e}")
            raise

    def get_programs(
        self, skip: int = 0, limit: int = 100, active_only: bool = True
    ) -> List[Program]:
        """Get list of programs with pagination"""
        try:
            query = self.db.query(Program)
            if active_only:
                query = query.filter(Program.is_active == True)

            programs = query.offset(skip).limit(limit).all()
            return programs
        except Exception as e:
            logger.error(f"Failed to get programs list: {e}")
            raise

    def get_programs_by_university(self, university_id: int) -> List[Program]:
        """Get all programs for a university"""
        try:
            programs = (
                self.db.query(Program)
                .filter(
                    Program.university_id == university_id, Program.is_active == True
                )
                .all()
            )
            return programs
        except Exception as e:
            logger.error(f"Failed to get programs for university {university_id}: {e}")
            raise

    def get_programs_by_field(self, field_of_study: str) -> List[Program]:
        """Get programs by field of study"""
        try:
            programs = (
                self.db.query(Program)
                .filter(
                    Program.field_of_study.ilike(f"%{field_of_study}%"),
                    Program.is_active == True,
                )
                .all()
            )
            return programs
        except Exception as e:
            logger.error(f"Failed to get programs for field {field_of_study}: {e}")
            raise

    def count_programs(self, active_only: bool = True) -> int:
        """Count total number of programs"""
        try:
            query = self.db.query(Program)
            if active_only:
                query = query.filter(Program.is_active == True)

            count = query.count()
            return count
        except Exception as e:
            logger.error(f"Failed to count programs: {e}")
            raise

    def delete_program(self, program_id: int) -> bool:
        """Soft delete program (set is_active to False)"""
        try:
            program = self.get_program_by_id(program_id)
            if not program:
                return False

            program.is_active = False
            self.db.commit()

            logger.info(f"Program soft deleted: {program.name}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete program {program_id}: {e}")
            raise

    def get_program_recommendations_by_field(
        self, field_of_study: str, limit: int = 10
    ) -> List[dict]:
        """Get program recommendations by field of study"""
        try:
            programs = (
                self.db.query(Program)
                .join(Program.university)
                .filter(
                    Program.field_of_study.ilike(f"%{field_of_study}%"),
                    Program.is_active == True,
                )
                .limit(limit)
                .all()
            )

            recommendations = []
            for program in programs:
                recommendations.append(
                    {
                        "program_id": program.id,
                        "program_name": program.name,
                        "university_name": program.university.name,
                        "field_of_study": program.field_of_study,
                        "degree_level": program.degree_level.value,
                        "match_score": 80.0,  # Base score for field match
                        "recommendation_reason": f"Matches field: {field_of_study}",
                    }
                )

            return recommendations
        except Exception as e:
            logger.error(
                f"Failed to get program recommendations for field {field_of_study}: {e}"
            )
            return []

    def get_programs_from_top_ranked_universities(
        self, top_n_universities: int = 10, limit_per_university: int = 5
    ) -> List[dict]:
        """
        Get programs offered by the highest world-ranked universities.

        Args:
            top_n_universities: How many top universities (by ranking_world ascending) to include
            limit_per_university: Max programs to return per university

        Returns:
            List of dict program summaries including university ranking metadata.
        """
        try:
            from app.models import University, Region

            # Select top N universities with a ranking_world value
            top_unis = (
                self.db.query(University)
                .filter(University.ranking_world.isnot(None))
                .order_by(University.ranking_world.asc())
                .limit(top_n_universities)
                .all()
            )

            results: List[dict] = []
            for uni in top_unis:
                programs = (
                    self.db.query(Program)
                    .join(Program.university)
                    .filter(Program.university_id == uni.id, Program.is_active == True)
                    .limit(limit_per_university)
                    .all()
                )
                for prog in programs:
                    results.append(
                        {
                            "program_id": prog.id,
                            "program_name": prog.name,
                            "degree_level": prog.degree_level.value if prog.degree_level else None,
                            "field_of_study": prog.field_of_study,
                            "language": prog.language,
                            "tuition_fee": float(prog.tuition_fee) if prog.tuition_fee is not None else None,
                            "currency": prog.currency,
                            "university_id": uni.id,
                            "university_name": uni.name,
                            "university_ranking_world": uni.ranking_world,
                            "university_ranking_national": uni.ranking_national,
                        }
                    )

            # Sort overall by university ranking then maybe future scoring
            results.sort(key=lambda r: (r["university_ranking_world"] or 1_000_000))
            return results
        except Exception as e:
            logger.error(
                f"Failed to get programs from top ranked universities: {e}"
            )
            return []

    def update_program(self, program_id: int, program_data: ProgramCreate) -> Optional[Program]:
        """Update program details and replace requirements"""
        try:
            program = self.get_program_by_id(program_id)
            if not program:
                return None

            # Update scalar fields
            update_fields = program_data.model_dump(exclude={"requirements"})
            for field, value in update_fields.items():
                setattr(program, field, value)

            # Replace requirements if provided
            if program_data.requirements is not None:
                # Delete existing
                for req in list(program.requirements):
                    self.db.delete(req)
                self.db.flush()
                # Add new
                for req_data in program_data.requirements:
                    new_req = ProgramRequirement(program_id=program.id, **req_data.model_dump())
                    self.db.add(new_req)

            self.db.commit()
            self.db.refresh(program)

            logger.info(f"Program updated successfully: {program.name}")
            return program
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to update program due to integrity constraint: {e}")
            raise ValueError("Invalid university ID or duplicate program")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update program {program_id}: {e}")
            raise
