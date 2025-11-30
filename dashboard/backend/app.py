from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from datetime import timedelta
from pathlib import Path

from config import get_settings
from auth import create_access_token, verify_token, hash_password
from database import db
from models import UserRegister, UserLogin, TokenResponse, UserResponse

settings = get_settings()
app = FastAPI(title="College-Bot Analytics API")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Authentication Endpoints ====================

@app.post("/api/auth/register", response_model=TokenResponse)
async def register(user_data: UserRegister):
    """Register a new user"""
    # Check if user exists
    existing_user = await db.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    new_user = await db.register_user(
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name
    )
    
    if not new_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed"
        )
    
    # Create token
    access_token = create_access_token(data={"sub": new_user["id"]})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(**new_user)
    )

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """Login user"""
    user = await db.verify_user_password(credentials.email, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    access_token = create_access_token(data={"sub": user["id"]})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(**user)
    )

@app.get("/api/auth/verify")
async def verify_token_endpoint(token_data: dict = Depends(verify_token)):
    """Verify JWT token"""
    return {"valid": True, "user_id": token_data["user_id"]}

# ==================== Dashboard Endpoints ====================

@app.get("/api/dashboard/metrics")
async def get_metrics(token_data: dict = Depends(verify_token)):
    """Get dashboard metrics for authenticated user"""
    metrics = await db.get_dashboard_metrics(token_data["user_id"])
    return {"metrics": metrics}

# ==================== Serve Frontend ====================

# Serve React frontend static files
frontend_path = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)