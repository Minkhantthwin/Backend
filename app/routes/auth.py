from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_mysql_session
from app.services.auth_service import AuthenticationService
from app.schemas import UserLogin, Token, UserResponse
from app.dependencies.auth import get_current_user
from app.models import User
from app.util.log import get_logger

logger = get_logger(__name__)
router = APIRouter()
security = HTTPBearer()


def get_auth_service(db: Session = Depends(get_mysql_session)) -> AuthenticationService:
    """Dependency to get authentication service"""
    return AuthenticationService(db)


@router.post(
    "/auth/login",
    response_model=Token,
    summary="User login",
    description="Authenticate user and return access token",
)
async def login(
    login_data: UserLogin,
    auth_service: AuthenticationService = Depends(get_auth_service),
):
    """
    Authenticate a user and return an access token.

    **Parameters:**
    - **email**: User's email address
    - **password**: User's password

    **Returns:**
    - **access_token**: JWT access token
    - **token_type**: Token type (bearer)
    - **expires_in**: Token expiration time in seconds
    - **user_id**: ID of the authenticated user
    - **email**: Email of the authenticated user

    **Example Request:**
    ```json
    {
        "email": "john.doe@example.com",
        "password": "StrongPassword123!"
    }
    ```

    **Example Response:**
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 1800,
        "user_id": 1,
        "email": "john.doe@example.com"
    }
    ```
    """
    try:
        token = auth_service.login(login_data)
        logger.info(f"User login successful: {login_data.email}")
        return token

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login",
        )


@router.post(
    "/auth/refresh",
    response_model=Token,
    summary="Refresh access token",
    description="Refresh an existing access token",
)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthenticationService = Depends(get_auth_service),
):
    """
    Refresh an existing access token.

    **Headers:**
    - **Authorization**: Bearer {your_current_token}

    **Returns:**
    - **access_token**: New JWT access token
    - **token_type**: Token type (bearer)
    - **expires_in**: Token expiration time in seconds
    - **user_id**: ID of the authenticated user
    - **email**: Email of the authenticated user

    **Example Response:**
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 1800,
        "user_id": 1,
        "email": "john.doe@example.com"
    }
    ```
    """
    try:
        token = credentials.credentials
        new_token = auth_service.refresh_token(token)
        logger.info("Token refresh successful")
        return new_token

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token refresh",
        )


@router.get(
    "/auth/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get the current authenticated user's information",
)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get the current authenticated user's information.

    **Headers:**
    - **Authorization**: Bearer {your_access_token}

    **Returns:**
    - Complete user information including qualifications, interests, and test scores

    **Example Response:**
    ```json
    {
        "id": 1,
        "email": "john.doe@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+1234567890",
        "date_of_birth": "1990-01-01",
        "nationality": "American",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
        "qualifications": [...],
        "interests": [...],
        "test_scores": [...]
    }
    ```
    """
    try:
        logger.info(f"Current user info requested: {current_user.email}")
        return current_user

    except Exception as e:
        logger.error(f"Error getting current user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error getting user information",
        )


@router.post(
    "/auth/logout",
    summary="User logout",
    description="Logout user (client-side token invalidation)",
)
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout the current user.

    **Note:** Since JWT tokens are stateless, this endpoint primarily serves
    as a confirmation of logout intent. The actual token invalidation should
    be handled on the client side by removing the token from storage.

    For enhanced security in production, you might want to implement:
    - Token blacklisting
    - Shorter token expiration times
    - Refresh token rotation

    **Headers:**
    - **Authorization**: Bearer {your_access_token}

    **Returns:**
    - Success message confirming logout
    """
    try:
        logger.info(f"User logout: {current_user.email}")
        return {
            "message": "Logout successful",
            "detail": "Please remove the token from client storage"
        }

    except Exception as e:
        logger.error(f"Error during logout: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during logout",
        )


@router.get(
    "/auth/verify",
    summary="Verify token",
    description="Verify if the current token is valid",
)
async def verify_token(current_user: User = Depends(get_current_user)):
    """
    Verify if the current access token is valid.

    **Headers:**
    - **Authorization**: Bearer {your_access_token}

    **Returns:**
    - Token validity status and basic user information

    **Example Response:**
    ```json
    {
        "valid": true,
        "user_id": 1,
        "email": "john.doe@example.com",
        "message": "Token is valid"
    }
    ```
    """
    try:
        return {
            "valid": True,
            "user_id": current_user.id,
            "email": current_user.email,
            "message": "Token is valid"
        }

    except Exception as e:
        logger.error(f"Error during token verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token verification",
        )
