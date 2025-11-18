"""
JWT Authentication module for fines-service
"""
from uuid import UUID
from typing import Optional
from fastapi import Header, HTTPException, status
from jose import jwt, JWTError
import logging

logger = logging.getLogger(__name__)

# JWT configuration (must match user-service settings)
JWT_SECRET_KEY = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"


def get_current_user_id(authorization: Optional[str] = Header(None)) -> UUID:
    """
    Extract and validate user_id from JWT token in Authorization header.
    
    Args:
        authorization: Authorization header value (Bearer <token>)
        
    Returns:
        UUID: Authenticated user's ID
        
    Raises:
        HTTPException: 401 if token is missing, invalid, or expired
    """
    if not authorization:
        logger.warning("Authorization header missing")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Extract token from "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.warning(f"Invalid authorization header format: {authorization}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = parts[1]
    
    try:
        # Decode and validate JWT token
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )
        
        # Extract user_id from "sub" field
        user_id_str: str = payload.get("sub")
        if not user_id_str:
            logger.warning("Token payload missing 'sub' field")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Convert to UUID
        user_id = UUID(user_id_str)
        logger.info(f"User authenticated: {user_id}")
        return user_id
        
    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except ValueError as e:
        logger.error(f"Failed to parse user_id as UUID: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: malformed user ID",
            headers={"WWW-Authenticate": "Bearer"}
        )

