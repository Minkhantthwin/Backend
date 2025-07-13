from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from app.models import UserTestScore
from app.schemas import UserTestScoreCreate
import logging

logger = logging.getLogger(__name__)


class UserTestScoreRepository:
    """Repository for user test score database operations"""

    def __init__(self, db: Session):
        self.db = db

    def create_test_score(
        self, user_id: int, test_score_data: UserTestScoreCreate
    ) -> UserTestScore:
        """Create a new user test score"""
        try:
            test_score_dict = test_score_data.model_dump()
            test_score_dict["user_id"] = user_id

            db_test_score = UserTestScore(**test_score_dict)
            self.db.add(db_test_score)
            self.db.commit()
            self.db.refresh(db_test_score)
            logger.info(f"User test score created successfully for user {user_id}")
            return db_test_score

        except IntegrityError as e:
            self.db.rollback()
            logger.error(
                f"Failed to create test score due to integrity constraint: {e}"
            )
            raise ValueError("Invalid user ID")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create test score: {e}")
            raise

    def get_test_score_by_id(self, test_score_id: int) -> Optional[UserTestScore]:
        """Get test score by ID"""
        try:
            test_score = (
                self.db.query(UserTestScore)
                .filter(UserTestScore.id == test_score_id)
                .first()
            )
            return test_score
        except Exception as e:
            logger.error(f"Failed to get test score by ID {test_score_id}: {e}")
            raise

    def get_test_scores_by_user(self, user_id: int) -> List[UserTestScore]:
        """Get all test scores for a user"""
        try:
            test_scores = (
                self.db.query(UserTestScore)
                .filter(UserTestScore.user_id == user_id)
                .all()
            )
            return test_scores
        except Exception as e:
            logger.error(f"Failed to get test scores for user {user_id}: {e}")
            raise

    def delete_test_score(self, test_score_id: int) -> bool:
        """Delete a test score"""
        try:
            test_score = self.get_test_score_by_id(test_score_id)
            if not test_score:
                return False

            self.db.delete(test_score)
            self.db.commit()
            logger.info(f"Test score deleted: {test_score_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete test score {test_score_id}: {e}")
            raise
