from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer # Import only HTTPBearer
from config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer() # Create an instance of HTTPBearer

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# Corrected function signature and logic
def verify_token(credentials: HTTPBearer = Depends(security)) -> dict: # Change type hint to HTTPBearer (or the actual type if available)
    """
    Dependency to verify the Bearer token and return user info.
    """
    # credentials is an object provided by FastAPI when using Depends(HTTPBearer())
    # It has attributes .credentials (the token string) and .scheme
    token = credentials.credentials # Extract the token string
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"user_id": user_id}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Example usage in a route (uncomment if needed for testing)
# from fastapi import FastAPI
# app = FastAPI()
#
# @app.get("/protected")
# async def protected_route(current_user: dict = Depends(verify_token)):
#     return {"message": "Hello, authenticated user!", "user": current_user}