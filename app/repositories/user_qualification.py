from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from app.models import UserQualification
from app.schemas import UserQualificationCreate
import logging

logger = logging.getLogger(__name__)


class UserQualificationRepository:
    """Repository for user qualification database operations"""

    def __init__(self, db: Session):
        self.db = db

    def create_qualification(
        self, user_id: int, qualification_data: UserQualificationCreate
    ) -> UserQualification:
        """Create a new user qualification"""
        try:
            qualification_dict = qualification_data.model_dump()
            qualification_dict["user_id"] = user_id

            db_qualification = UserQualification(**qualification_dict)
            self.db.add(db_qualification)
            self.db.commit()
            self.db.refresh(db_qualification)
            logger.info(f"User qualification created successfully for user {user_id}")
            return db_qualification

        except IntegrityError as e:
            self.db.rollback()
            logger.error(
                f"Failed to create qualification due to integrity constraint: {e}"
            )
            raise ValueError("Invalid user ID or duplicate qualification")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create qualification: {e}")
            raise

    def get_qualification_by_id(
        self, qualification_id: int
    ) -> Optional[UserQualification]:
        """Get qualification by ID"""
        try:
            qualification = (
                self.db.query(UserQualification)
                .filter(UserQualification.id == qualification_id)
                .first()
            )
            return qualification
        except Exception as e:
            logger.error(f"Failed to get qualification by ID {qualification_id}: {e}")
            raise

    def get_qualifications_by_user(self, user_id: int) -> List[UserQualification]:
        """Get all qualifications for a user"""
        try:
            qualifications = (
                self.db.query(UserQualification)
                .filter(UserQualification.user_id == user_id)
                .all()
            )
            return qualifications
        except Exception as e:
            logger.error(f"Failed to get qualifications for user {user_id}: {e}")
            raise

    def delete_qualification(self, qualification_id: int) -> bool:
        """Delete a qualification"""
        try:
            qualification = self.get_qualification_by_id(qualification_id)
            if not qualification:
                return False

            self.db.delete(qualification)
            self.db.commit()
            logger.info(f"Qualification deleted: {qualification_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete qualification {qualification_id}: {e}")
            raise
