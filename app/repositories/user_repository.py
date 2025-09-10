from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from app.models import User, UserQualification, UserInterest, UserTestScore
from app.schemas import UserCreate, UserUpdate
from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRepository:
    """Repository for user database operations"""

    def __init__(self, db: Session):
        self.db = db

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
            # Security: prevent privilege escalation during open registration
            user_dict["is_admin"] = False

            db_user = User(**user_dict)
            self.db.add(db_user)
            self.db.flush()  # Get user ID without committing

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

    def create_admin_user(self, user_data: UserCreate) -> User:
        """Create a new admin user - allows is_admin to be set to True"""
        try:
            # Hash password
            hashed_password = self._hash_password(user_data.password)

            # Create user object without nested data
            user_dict = user_data.model_dump(
                exclude={"password", "qualifications", "interests", "test_scores"}
            )
            user_dict["password_hash"] = hashed_password
            # Allow admin creation for this method
            user_dict["is_admin"] = True

            db_user = User(**user_dict)
            self.db.add(db_user)
            self.db.flush()  # Get user ID without committing

            # Admin users typically don't need interests or test scores
            # Only add if explicitly provided

            self.db.commit()
            self.db.refresh(db_user)

            logger.info(f"Admin user created successfully: {db_user.email}")
            return db_user

        except IntegrityError as e:
            self.db.rollback()
            logger.error(
                f"Failed to create admin user due to integrity constraint: {e}"
            )
            raise ValueError("Admin user with this email already exists")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create admin user: {e}")
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

            logger.info(f"User permanently deleted: {user.email}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete user {user_id}: {e}")
            raise
