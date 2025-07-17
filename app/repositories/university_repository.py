from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from app.models import University
from app.schemas import UniversityCreate
from app.services.neo4j_program_service import Neo4jProgramService
import logging

logger = logging.getLogger(__name__)


class UniversityRepository:
    """Repository for university database operations"""

    def __init__(self, db: Session):
        self.db = db
        self.neo4j_service = Neo4jProgramService()

    def create_university(self, university_data: UniversityCreate) -> University:
        try:
            db_university = University(**university_data.model_dump())
            self.db.add(db_university)
            self.db.commit()
            self.db.refresh(db_university)
            
            # Create university node in Neo4j
            try:
                self.neo4j_service.create_university_node(db_university)
            except Exception as neo4j_error:
                logger.warning(f"Failed to create university in Neo4j: {neo4j_error}")
                # Don't fail the entire operation if Neo4j fails
            
            logger.info(f"University created successfully: {db_university.name}")
            return db_university
        except IntegrityError as e:
            self.db.rollback()
            logger.error(
                f"Failed to create university due to integrity constraint: {e}"
            )
            raise ValueError("University name already exists or invalid region_id")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create university: {e}")
            raise

    def get_university_by_id(self, university_id: int) -> Optional[University]:
        try:
            university = (
                self.db.query(University).filter(University.id == university_id).first()
            )
            return university
        except Exception as e:
            logger.error(f"Failed to get university by ID {university_id}: {e}")
            raise

    def get_universities(
        self, skip: int = 0, limit: int = 100, region_id: Optional[int] = None
    ) -> List[University]:
        try:
            query = self.db.query(University)
            if region_id:
                query = query.filter(University.region_id == region_id)
            universities = query.offset(skip).limit(limit).all()
            return universities
        except Exception as e:
            logger.error(f"Failed to get universities list: {e}")
            raise

    def update_university(
        self, university_id: int, university_data: UniversityCreate
    ) -> Optional[University]:
        try:
            university = self.get_university_by_id(university_id)
            if not university:
                return None
            for field, value in university_data.model_dump().items():
                setattr(university, field, value)
            self.db.commit()
            self.db.refresh(university)
            
            # Update university node in Neo4j
            try:
                self.neo4j_service.update_university_node(university)
            except Exception as neo4j_error:
                logger.warning(f"Failed to update university in Neo4j: {neo4j_error}")
                # Don't fail the entire operation if Neo4j fails
            
            logger.info(f"University updated successfully: {university.name}")
            return university
        except IntegrityError as e:
            self.db.rollback()
            logger.error(
                f"Failed to update university due to integrity constraint: {e}"
            )
            raise ValueError("University name already exists or invalid region_id")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update university {university_id}: {e}")
            raise

    def delete_university(self, university_id: int) -> bool:
        try:
            university = self.get_university_by_id(university_id)
            if not university:
                return False
            self.db.delete(university)
            self.db.commit()
            
            # Delete university node from Neo4j
            try:
                self.neo4j_service.delete_university_node(university_id)
            except Exception as neo4j_error:
                logger.warning(f"Failed to delete university from Neo4j: {neo4j_error}")
                # Don't fail the entire operation if Neo4j fails
            
            logger.info(f"University deleted: {university_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete university {university_id}: {e}")
            raise

    def search_universities_by_name(self, name: str) -> List[University]:
        try:
            universities = (
                self.db.query(University)
                .filter(University.name.ilike(f"%{name}%"))
                .all()
            )
            return universities
        except Exception as e:
            logger.error(f"Failed to search universities by name {name}: {e}")
            raise

    def get_universities_by_region_neo4j(self, region_id: int) -> List[dict]:
        """Get universities by region from Neo4j"""
        try:
            return self.neo4j_service.get_universities_by_region(region_id)
        except Exception as e:
            logger.error(f"Failed to get universities by region {region_id} from Neo4j: {e}")
            return []
