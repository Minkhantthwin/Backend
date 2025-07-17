from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from app.models import User, UserQualification, UserInterest, UserTestScore
from app.schemas import UserCreate, UserUpdate
from app.services.neo4j_user_service import Neo4jUserService
from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRepository:
    """Repository for user database operations"""

    def __init__(self, db: Session):
        self.db = db
        self.neo4j_service = Neo4jUserService()

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user with qualifications, interests, and test scores"""
        try:
            # Hash password
            hashed_password = self._hash_password(user_data.password)

            # Create user object without nested data
            user_dict = user_data.model_dump(
                exclude={"password", "qualifications", "interests", "test_scores"}
            )
            user_dict["password_hash"] = hashed_password

            db_user = User(**user_dict)
            self.db.add(db_user)
            self.db.flush()  # Get user ID without committing

            # Add qualifications
            if user_data.qualifications:
                for qual_data in user_data.qualifications:
                    qualification = UserQualification(
                        user_id=db_user.id, **qual_data.model_dump()
                    )
                    self.db.add(qualification)

            # Add interests
            if user_data.interests:
                for interest_data in user_data.interests:
                    interest = UserInterest(
                        user_id=db_user.id, **interest_data.model_dump()
                    )
                    self.db.add(interest)

            # Add test scores
            if user_data.test_scores:
                for score_data in user_data.test_scores:
                    test_score = UserTestScore(
                        user_id=db_user.id, **score_data.model_dump()
                    )
                    self.db.add(test_score)

            self.db.commit()
            self.db.refresh(db_user)
            
            # Create user node in Neo4j for recommendations
            try:
                self.neo4j_service.create_user_node(db_user)
            except Exception as neo4j_error:
                logger.warning(f"Failed to create user in Neo4j: {neo4j_error}")
                # Don't fail the entire operation if Neo4j fails
            
            logger.info(f"User created successfully: {db_user.email}")
            return db_user

        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to create user due to integrity constraint: {e}")
            raise ValueError("User with this email already exists")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create user: {e}")
            raise

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            return user
        except Exception as e:
            logger.error(f"Failed to get user by ID {user_id}: {e}")
            raise

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            user = self.db.query(User).filter(User.email == email).first()
            return user
        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {e}")
            raise

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username - removed as username field doesn't exist in model"""
        logger.warning(
            "get_user_by_username called but username field doesn't exist in User model"
        )
        return None

    def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get list of users with pagination"""
        try:
            users = self.db.query(User).offset(skip).limit(limit).all()
            return users
        except Exception as e:
            logger.error(f"Failed to get users list: {e}")
            raise

    def count_users(self) -> int:
        """Count total number of users"""
        try:
            count = self.db.query(User).count()
            return count
        except Exception as e:
            logger.error(f"Failed to count users: {e}")
            raise

    def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Update user information"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return None

            # Update only provided fields
            update_data = user_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(user, field, value)

            self.db.commit()
            self.db.refresh(user)
            
            # Update user node in Neo4j
            try:
                self.neo4j_service.update_user_node(user)
            except Exception as neo4j_error:
                logger.warning(f"Failed to update user in Neo4j: {neo4j_error}")
                # Don't fail the entire operation if Neo4j fails
            
            logger.info(f"User updated successfully: {user.email}")
            return user
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to update user due to integrity constraint: {e}")
            raise ValueError("Email already exists")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update user {user_id}: {e}")
            raise

    def delete_user(self, user_id: int) -> bool:
        """Permanently delete user from database"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False

            self.db.delete(user)
            self.db.commit()
            
            # Delete user node from Neo4j
            try:
                self.neo4j_service.delete_user_node(user_id)
            except Exception as neo4j_error:
                logger.warning(f"Failed to delete user from Neo4j: {neo4j_error}")
                # Don't fail the entire operation if Neo4j fails
            
            logger.info(f"User permanently deleted: {user.email}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete user {user_id}: {e}")
            raise

    def get_user_recommendations(self, user_id: int, limit: int = 10) -> List[dict]:
        """Get program recommendations for a user from Neo4j"""
        try:
            return self.neo4j_service.get_user_recommendations(user_id, limit)
        except Exception as e:
            logger.error(f"Failed to get user recommendations for {user_id}: {e}")
            return []
