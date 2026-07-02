import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.rate_limit import apply_rate_limit
from app.core.sanitize import ensure_present, sanitize_text
from app.core.security import create_access_token, decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import AuthResponse, UserLogin
from app.schemas.user import UserCreate, UserRead
from app.services.auth import authenticate_user, create_user, get_user_by_email, verify_password

logger = logging.getLogger(__name__)
router = APIRouter()




@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthResponse:
    """
    Register a new user account.
    
    Args:
        payload: User creation data with validated password
        request: FastAPI request object for rate limiting
        response: FastAPI response object for setting cookies
        db: Database session
        
    Returns:
        AuthResponse: Created user data with success message
        
    Raises:
        HTTPException: If registration fails due to validation or existing email
    """
    apply_rate_limit(request, scope="auth-register", limit=5)
    payload.name = ensure_present(sanitize_text(payload.name, max_length=255), field_name="name")
    payload.email = ensure_present(sanitize_text(payload.email, max_length=255).lower(), field_name="email")

    if get_user_by_email(db, payload.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    try:
        user = create_user(db, payload)
    except ValueError as e:
        # Handle password hashing errors (e.g., bcrypt limit exceeded)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=86400,
    )
    return AuthResponse(
        user=UserRead.model_validate(user), 
        access_token=access_token,
        token_type="bearer",
        message="Account created."
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthResponse:
    """
    Authenticate a user and create a session.
    
    Args:
        payload: User login credentials with validated password
        request: FastAPI request object for rate limiting
        response: FastAPI response object for setting cookies
        db: Database session
        
    Returns:
        AuthResponse: Authenticated user data with success message
        
    Raises:
        HTTPException: If authentication fails due to invalid credentials
    """
    apply_rate_limit(request, scope="auth-login", limit=8)
    email_clean = ensure_present(sanitize_text(payload.email, max_length=255).lower(), field_name="email")
    
    try:
        # 1. Check if user is found by email in the database
        user_in_db = get_user_by_email(db, email_clean)
        if not user_in_db:
            logger.warning("Login check: User NOT found by email '%s' in database.", email_clean)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        
        logger.info("Login check: User found by email '%s' in database.", email_clean)
        
        # 2. Check password verification
        password_verified = verify_password(payload.password, user_in_db.hashed_password)
        if not password_verified:
            logger.warning("Login check: Password verification failed (bcrypt mismatch) for email '%s'.", email_clean)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password",
            )
            
        logger.info("Login check: Password verification passed (bcrypt match) for email '%s'.", email_clean)
        
        # 3. Check if user is active (default to True)
        is_active = getattr(user_in_db, "is_active", True)
        if not is_active:
            logger.warning("Login check: Account is inactive for email '%s'.", email_clean)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account inactive",
            )

        user = user_in_db
            
    except HTTPException:
        # Re-raise standard HTTP exceptions
        raise
    except Exception as e:
        # 3. Log the exact exception if any is raised
        logger.exception("Login error: Exact exception raised during authentication: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during authentication.",
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=86400,
    )
    return AuthResponse(
        user=UserRead.model_validate(user), 
        access_token=access_token,
        token_type="bearer",
        message="Logged in successfully."
    )




@router.post("/refresh", response_model=AuthResponse)
async def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthResponse:
    """
    Refresh the authentication token.
    
    Args:
        request: FastAPI request object for reading cookies
        response: FastAPI response object for setting cookies
        db: Database session
        
    Returns:
        AuthResponse: Authenticated user data with success message
        
    Raises:
        HTTPException: If refresh fails due to invalid token
    """
    try:
        # Check cookie first
        token = request.cookies.get("access_token")
        
        # Fallback to Authorization header
        if not token:
            authorization = request.headers.get("Authorization")
            if authorization and authorization.startswith("Bearer "):
                token = authorization.split(" ")[1]
                
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No access token found.",
            )
        
        payload = decode_access_token(token)
        if not payload or "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token.",
            )
        
        user_id = payload["sub"]
        
        # Try parsing UUID and query db
        try:
            import uuid
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid subject identifier.",
            )
            
        user = db.get(User, user_uuid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found.",
            )
        
        new_token = create_access_token(data={"sub": str(user.id)})
        response.set_cookie(
            key="access_token",
            value=new_token,
            httponly=True,
            secure=True,
            samesite="none",
            max_age=86400,
        )
        return AuthResponse(
            user=UserRead.model_validate(user), 
            access_token=new_token,
            token_type="bearer",
            message="Token refreshed."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Refresh error: Exact exception raised during token refresh: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed.",
        )


@router.post("/logout")
async def logout(response: Response) -> dict[str, str]:
    """
    Log out the current user.
    """
    response.delete_cookie(key="access_token", samesite="none", secure=True)
    return {"message": "Logged out successfully."}


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)) -> UserRead:
    """
    Get the current authenticated user's information.
    
    Args:
        current_user: The authenticated user from dependency injection
        
    Returns:
        UserRead: Current user's data
    """
    return UserRead.model_validate(current_user)
