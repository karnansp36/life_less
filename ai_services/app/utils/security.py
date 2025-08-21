# In app/utils/security.py
from fastapi import Header, HTTPException, status

def validate_token(authorization: str = Header(None)):
    """
    Microservice stub - assumes API Gateway already validated the token
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing authorization header"
        )
    
    # Just extract user ID from header (assuming API Gateway passed it)
    # In real setup, you might get user info from headers like:
    # X-User-ID, X-User-Roles, etc.
    token = authorization.replace("Bearer ", "")
    
    # For now, just return a basic user object
    return {"sub": "user_id_from_gateway", "token": token}