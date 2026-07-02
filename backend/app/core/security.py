import logging
import warnings
from datetime import datetime, timedelta
from typing import Optional

import jwt

# Suppress passlib's bcrypt version-detection warning.
# passlib 1.7.4 calls bcrypt.__about__.__version__ which doesn't exist in
# newer bcrypt releases — the hash/verify still works correctly.
logging.getLogger("passlib").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", message=".*bcrypt.*", category=UserWarning)

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from passlib.context import CryptContext

from app.core.config import settings

# Use bcrypt with secure defaults and explicit backend
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
    bcrypt__ident="2b",  # Use 2b ident to avoid wrap bug detection
)



def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: The plain text password to verify
        hashed_password: The bcrypt hash to verify against
        
    Returns:
        bool: True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: The plain text password to hash
        
    Returns:
        str: The bcrypt hash of the password
        
    Raises:
        ValueError: If password exceeds bcrypt's 72-byte limit
    """
    # Check byte length before hashing (bcrypt has 72-byte limit)
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        raise ValueError(
            "Password exceeds maximum allowed length of 72 bytes. "
            "Please use a shorter password."
        )
    
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: The payload data to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        str: The encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRES_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def decode_access_token(token: str, verify_exp: bool = True) -> Optional[dict]:
    """
    Decode and verify a JWT access token.
    
    Args:
        token: The JWT token to decode
        verify_exp: Whether to verify token expiration
        
    Returns:
        Optional[dict]: The decoded payload if valid, None otherwise
    """
    try:
        options = {}
        if not verify_exp:
            options["verify_exp"] = False
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=["HS256"],
            options=options,
        )
        return payload
    except jwt.PyJWTError:
        return None
