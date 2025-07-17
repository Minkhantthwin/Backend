from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from app.models import Program, ProgramRequirement
from app.schemas import ProgramCreate
from app.services.neo4j_program_service import Neo4jProgramService
import logging

logger = logging.getLogger(__name__)


class ProgramRepository:
    """Repository for program database operations"""

    def __init__(self, db: Session):
        self.db = db
        self.neo4j_service = Neo4jProgramService()

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
            
            # Create program node in Neo4j
            try:
                self.neo4j_service.create_program_node(db_program)
            except Exception as neo4j_error:
                logger.warning(f"Failed to create program in Neo4j: {neo4j_error}")
                # Don't fail the entire operation if Neo4j fails
            
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
            
            # Update program node in Neo4j
            try:
                self.neo4j_service.delete_program_node(program_id)
            except Exception as neo4j_error:
                logger.warning(f"Failed to delete program in Neo4j: {neo4j_error}")
                # Don't fail the entire operation if Neo4j fails
            
            logger.info(f"Program soft deleted: {program.name}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete program {program_id}: {e}")
            raise

    def get_program_recommendations_by_field(self, field_of_study: str, limit: int = 10) -> List[dict]:
        """Get program recommendations by field of study from Neo4j"""
        try:
            return self.neo4j_service.get_program_recommendations_by_field(field_of_study, limit)
        except Exception as e:
            logger.error(f"Failed to get program recommendations for field {field_of_study}: {e}")
            return []
