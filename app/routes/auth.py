from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
import asyncio

from app.database import get_mysql_session
from app.services.auth_service import AuthenticationService
from app.services.qualification_service import QualificationService
from app.schemas import UserLogin, Token, UserResponse, UserCreate
from app.dependencies.auth import get_current_user
from app.models import User
from app.repositories.user_repository import UserRepository
from app.util.log import get_logger

logger = get_logger(__name__)
router = APIRouter()
security = HTTPBearer()


def get_auth_service(db: Session = Depends(get_mysql_session)) -> AuthenticationService:
    """Dependency to get authentication service"""
    return AuthenticationService(db)


def get_qualification_service(db: Session = Depends(get_mysql_session)) -> QualificationService:
    """Dependency to get qualification service"""
    return QualificationService(db)


async def update_user_qualifications_background(user_id: int, user_email: str):
    """Background task to update user qualifications after login"""
    try:
        # Create a new database session for the background task
        from app.database import get_database_manager
        db_manager = get_database_manager()
        
        with db_manager.mysql.get_db_session() as db:
            qualification_service = QualificationService(db)
            logger.info(f"Starting background qualification check for user {user_id} ({user_email})")
            
            qualification_results = qualification_service.check_user_against_all_programs(user_id)
            logger.info(f"Background qualification check completed for user {user_id}: {len(qualification_results)} programs processed")
            
    except Exception as e:
        logger.error(f"Error in background qualification update for user {user_id}: {e}")


@router.post(
    "/auth/login",
    response_model=Token,
    summary="User login",
    description="Authenticate user, return access token, and update qualification status",
)
async def login(
    login_data: UserLogin,
    auth_service: AuthenticationService = Depends(get_auth_service),
):
    """
    Authenticate a user and return an access token.
    
    This endpoint also automatically updates the user's qualification status
    against all programs to ensure recommendations are based on current data.
    """
    try:
        token = auth_service.login(login_data)
        logger.info(f"User login successful: {login_data.email}, token generated for user_id: {token.user_id}")
        
        # Start background task to update user qualifications
        asyncio.create_task(update_user_qualifications_background(token.user_id, token.email))
        logger.info(f"Started background qualification update for user {token.user_id}")
        
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
            "detail": "Please remove the token from client storage",
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
    """
    try:
        logger.info(f"Token verification successful for user: {current_user.email}")
        return {
            "valid": True,
            "user_id": current_user.id,
            "email": current_user.email,
            "is_admin": current_user.is_admin,
            "message": "Token is valid",
        }

    except Exception as e:
        logger.error(f"Error during token verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token verification",
        )


@router.post(
    "/auth/admin/register",
    response_model=UserResponse,
    summary="Admin registration",
    description="Create a new administrator account",
)
async def admin_register(
    user_data: UserCreate,
    db: Session = Depends(get_mysql_session),
):
    """
    Create a new administrator account.

    **Note:** This endpoint should be secured or disabled in production.
    Consider implementing proper admin invitation flows.
    """
    try:
        user_repo = UserRepository(db)
        new_admin = user_repo.create_admin_user(user_data)
        logger.info(f"Admin user registered successfully: {new_admin.email}")
        return new_admin

    except ValueError as e:
        logger.warning(f"Admin registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error during admin registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during admin registration",
        )
