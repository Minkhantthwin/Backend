from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from app.models import UserInterest
from app.schemas import UserInterestCreate
import logging

logger = logging.getLogger(__name__)


class UserInterestRepository:
    """Repository for user interest database operations"""

    def __init__(self, db: Session):
        self.db = db

    def create_interest(
        self, user_id: int, interest_data: UserInterestCreate
    ) -> UserInterest:
        """Create a new user interest"""
        try:
            interest_dict = interest_data.model_dump()
            interest_dict["user_id"] = user_id

            db_interest = UserInterest(**interest_dict)
            self.db.add(db_interest)
            self.db.commit()
            self.db.refresh(db_interest)

            logger.info(f"User interest created successfully for user {user_id}")
            return db_interest

        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to create interest due to integrity constraint: {e}")
            raise ValueError("Invalid user ID")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create interest: {e}")
            raise

    def get_interest_by_id(self, interest_id: int) -> Optional[UserInterest]:
        """Get interest by ID"""
        try:
            interest = (
                self.db.query(UserInterest)
                .filter(UserInterest.id == interest_id)
                .first()
            )
            return interest
        except Exception as e:
            logger.error(f"Failed to get interest by ID {interest_id}: {e}")
            raise

    def get_interests_by_user(self, user_id: int) -> List[UserInterest]:
        """Get all interests for a user"""
        try:
            interests = (
                self.db.query(UserInterest)
                .filter(UserInterest.user_id == user_id)
                .all()
            )
            return interests
        except Exception as e:
            logger.error(f"Failed to get interests for user {user_id}: {e}")
            raise

    def delete_interest(self, interest_id: int) -> bool:
        """Delete an interest"""
        try:
            interest = self.get_interest_by_id(interest_id)
            if not interest:
                return False

            self.db.delete(interest)
            self.db.commit()

            logger.info(f"Interest deleted: {interest_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete interest {interest_id}: {e}")
            raise

    def update_interest(
        self, interest_id: int, interest_data: UserInterestCreate
    ) -> Optional[UserInterest]:
        """Update an existing interest"""
        try:
            interest = self.get_interest_by_id(interest_id)
            if not interest:
                return None

            # Update MySQL
            for field, value in interest_data.model_dump().items():
                setattr(interest, field, value)

            self.db.commit()
            self.db.refresh(interest)

            logger.info(f"Interest updated successfully: {interest_id}")
            return interest

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update interest {interest_id}: {e}")
            raise
