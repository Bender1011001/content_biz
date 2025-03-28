"""
Authentication service for the content creation application.

For testing purposes, this implements simple dummy authentication.
In a production environment, this would use JWT or OAuth.
"""

import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

logger = logging.getLogger(__name__)

# Dummy authentication - would be replaced with proper JWT validation in production
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Test users/tokens for demo purposes
ADMIN_TOKEN = "admin-test-token-123"
USER_TOKENS = {
    "user-token-123": {"id": "user1", "email": "test@example.com", "name": "Test User"}
}


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Validate the user's token and return user information.
    
    In a real implementation, this would validate a JWT token.
    For testing, it checks against predefined tokens.
    """
    if token == ADMIN_TOKEN:
        return {"id": "admin1", "email": "admin@example.com", "name": "Admin User", "is_admin": True}
    
    if token in USER_TOKENS:
        return USER_TOKENS[token]
        
    logger.warning(f"Invalid authentication token: {token}")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_admin_user(current_user: dict = Depends(get_current_user)):
    """
    Verify the user has admin privileges.
    
    This dependency should be used on admin-only endpoints.
    """
    if not current_user.get("is_admin", False):
        logger.warning(f"Non-admin user attempted to access admin endpoint: {current_user.get('id')}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user
