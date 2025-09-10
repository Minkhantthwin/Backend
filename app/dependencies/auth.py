from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_mysql_session
from app.services.auth_service import AuthenticationService
from app.models import User
from app.util.log import get_logger

logger = get_logger(__name__)

# Security scheme for Bearer token - make it optional by default
security = HTTPBearer(auto_error=False)


def get_auth_service(db: Session = Depends(get_mysql_session)) -> AuthenticationService:
    """Dependency to get authentication service"""
    return AuthenticationService(db)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthenticationService = Depends(get_auth_service),
) -> User:
    """
    Dependency to get the current authenticated user.

    This dependency extracts the Bearer token from the Authorization header,
    verifies it, and returns the current user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials:
        logger.warning("No credentials provided")
        raise credentials_exception

    try:
        # Extract token from credentials
        token = credentials.credentials

        # Get user from token
        user = auth_service.get_current_user(token)

        if user is None:
            logger.warning("Authentication failed: Invalid token or user not found")
            raise credentials_exception

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_current_user dependency: {e}")
        raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to get the current active authenticated user.

    This extends get_current_user to also check if the user account is active.
    Currently, all users are considered active, but this can be extended
    to include user status checks if needed.
    """
    # Note: If you add an 'is_active' field to your User model in the future,
    # you can add the check here:
    # if not current_user.is_active:
    #     raise HTTPException(status_code=400, detail="Inactive user")

    return current_user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthenticationService = Depends(get_auth_service),
) -> Optional[User]:
    """
    Dependency to optionally get the current authenticated user.

    This dependency doesn't raise an exception if no token is provided
    or if the token is invalid. It returns None in such cases.
    Useful for endpoints that work for both authenticated and anonymous users.
    """
    if not credentials:
        return None

    try:
        token = credentials.credentials
        user = auth_service.get_current_user(token)
        return user

    except Exception as e:
        logger.warning(f"Optional authentication failed: {e}")
        return None


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to require admin privileges.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions - admin access required",
        )

    return current_user


def require_user_or_admin(
    target_user_id: int, current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to require that the current user is either the target user
    or an admin.

    This is useful for endpoints where users can only access their own data
    unless they're administrators.
    """
    # Check if user is accessing their own data
    if current_user.id == target_user_id:
        return current_user

    # Check if user is admin
    if current_user.is_admin:
        return current_user

    # User is not accessing their own data and is not admin
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not enough permissions to access this resource",
    )
