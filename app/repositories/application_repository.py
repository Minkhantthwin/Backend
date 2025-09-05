from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from typing import Optional, List
from app.models import Application
from app.schemas import ApplicationCreate, ApplicationUpdate
import logging

logger = logging.getLogger(__name__)


class ApplicationRepository:
    """Repository for application database operations"""

    def __init__(self, db: Session):
        self.db = db

    def create_application(self, application_data: ApplicationCreate) -> Application:
        """Create a new application"""
        try:
            db_application = Application(**application_data.model_dump())
            self.db.add(db_application)
            self.db.commit()
            self.db.refresh(db_application)
            logger.info(
                f"Application created successfully for user {application_data.user_id}"
            )
            return db_application

        except IntegrityError as e:
            self.db.rollback()
            logger.error(
                f"Failed to create application due to integrity constraint: {e}"
            )
            raise ValueError("Invalid user ID, program ID, or duplicate application")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create application: {e}")
            raise

    def get_application_by_id(self, application_id: int) -> Optional[Application]:
        """Get application by ID with relationships"""
        try:
            application = (
                self.db.query(Application)
                .filter(Application.id == application_id)
                .first()
            )
            return application
        except Exception as e:
            logger.error(f"Failed to get application by ID {application_id}: {e}")
            raise

    def get_applications_by_user(self, user_id: int) -> List[Application]:
        """Get all applications for a user"""
        try:
            applications = (
                self.db.query(Application).filter(Application.user_id == user_id).all()
            )
            return applications
        except Exception as e:
            logger.error(f"Failed to get applications for user {user_id}: {e}")
            raise

    def get_applications_by_program(self, program_id: int) -> List[Application]:
        """Get all applications for a program"""
        try:
            applications = (
                self.db.query(Application)
                .filter(Application.program_id == program_id)
                .all()
            )
            return applications
        except Exception as e:
            logger.error(f"Failed to get applications for program {program_id}: {e}")
            raise

    def update_application(
        self, application_id: int, application_data: ApplicationUpdate
    ) -> Optional[Application]:
        """Update application information"""
        try:
            application = self.get_application_by_id(application_id)
            if not application:
                return None

            # Update only provided fields
            update_data = application_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(application, field, value)

            self.db.commit()
            self.db.refresh(application)
            logger.info(f"Application updated successfully: {application_id}")
            return application
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update application {application_id}: {e}")
            raise

    def delete_application(self, application_id: int) -> bool:
        """Delete an application"""
        try:
            application = self.get_application_by_id(application_id)
            if not application:
                return False

            self.db.delete(application)
            self.db.commit()
            logger.info(f"Application deleted: {application_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete application {application_id}: {e}")
            raise

    def get_applications(self, skip: int = 0, limit: int = 100) -> List[Application]:
        """Get list of applications with pagination"""
        try:
            applications = self.db.query(Application).offset(skip).limit(limit).all()
            return applications
        except Exception as e:
            logger.error(f"Failed to get applications list: {e}")
            raise

    def count_applications(self) -> int:
        """Count total number of applications"""
        try:
            count = self.db.query(Application).count()
            return count
        except Exception as e:
            logger.error(f"Failed to count applications: {e}")
            raise

    def get_status_counts(self) -> dict:
        """Return counts by application status."""
        try:
            rows = (
                self.db.query(Application.status, func.count(Application.id))
                .group_by(Application.status)
                .all()
            )
            data = {status.name.lower(): count for status, count in rows}
            data["total"] = sum(data.values())
            return data
        except Exception as e:
            logger.error(f"Failed to get application status counts: {e}")
            raise
