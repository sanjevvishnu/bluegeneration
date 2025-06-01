"""
User API Endpoints
Provides authenticated user endpoints for the frontend
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from clerk_user_service import clerk_user_service

# Configure logging
logger = logging.getLogger(__name__)

# Create router for user endpoints
user_router = APIRouter(prefix="/api/user", tags=["user"])

# Pydantic models for request/response
class UserProfile(BaseModel):
    experience_level: Optional[str] = None
    target_companies: Optional[List[str]] = None
    subscription_tier: Optional[str] = None

class UserStats(BaseModel):
    total_interviews: int
    completed_interviews: int
    average_score: float
    current_streak: int
    subscription_tier: str
    interviews_used_this_month: int

class ConversationResponse(BaseModel):
    id: str
    session_id: str
    mode: str
    status: str
    title: Optional[str]
    duration: Optional[int]
    performance_score: Optional[float]
    difficulty_level: str
    created_at: str
    completed_at: Optional[str]

def get_clerk_user_id(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract Clerk user ID from Authorization header
    
    In a production app, you would validate the JWT token here.
    For development, we'll accept a simple format like "Bearer user_xxx"
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    # Extract user ID (in production, this would be from JWT validation)
    token = authorization[7:]  # Remove "Bearer "
    
    # For development, accept format like "user_xxx" or actual JWT
    if token.startswith("user_"):
        return token
    
    # TODO: In production, validate JWT and extract user ID
    # For now, just return the token as user ID
    return token

@user_router.get("/profile")
async def get_user_profile(clerk_user_id: str = Depends(get_clerk_user_id)) -> Dict[str, Any]:
    """Get user profile information"""
    try:
        user = clerk_user_service.get_user_by_clerk_id(clerk_user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "id": user["id"],
            "clerk_user_id": user["clerk_user_id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "experience_level": user["experience_level"],
            "target_companies": user["target_companies"],
            "subscription_tier": user["subscription_tier"],
            "interviews_used_this_month": user["interviews_used_this_month"],
            "created_at": user["created_at"],
            "updated_at": user["updated_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@user_router.put("/profile")
async def update_user_profile(
    profile_data: UserProfile,
    clerk_user_id: str = Depends(get_clerk_user_id)
) -> Dict[str, Any]:
    """Update user profile information"""
    try:
        # Prepare update data
        update_data = {}
        if profile_data.experience_level:
            update_data["experience_level"] = profile_data.experience_level
        if profile_data.target_companies is not None:
            update_data["target_companies"] = profile_data.target_companies
        if profile_data.subscription_tier:
            update_data["subscription_tier"] = profile_data.subscription_tier
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No data to update")
        
        user = clerk_user_service.update_user(clerk_user_id, update_data)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "status": "success",
            "message": "Profile updated successfully",
            "user": {
                "id": user["id"],
                "experience_level": user["experience_level"],
                "target_companies": user["target_companies"],
                "subscription_tier": user["subscription_tier"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@user_router.get("/stats")
async def get_user_stats(clerk_user_id: str = Depends(get_clerk_user_id)) -> UserStats:
    """Get user interview statistics"""
    try:
        stats = clerk_user_service.get_user_stats(clerk_user_id)
        
        if not stats:
            # Return default stats for new users
            return UserStats(
                total_interviews=0,
                completed_interviews=0,
                average_score=0.0,
                current_streak=0,
                subscription_tier="free",
                interviews_used_this_month=0
            )
        
        return UserStats(**stats)
        
    except Exception as e:
        logger.error(f"Error getting user stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@user_router.get("/conversations")
async def get_user_conversations(
    limit: int = 10,
    clerk_user_id: str = Depends(get_clerk_user_id)
) -> List[ConversationResponse]:
    """Get user's recent conversations"""
    try:
        conversations = clerk_user_service.get_user_conversations(clerk_user_id, limit)
        
        return [
            ConversationResponse(
                id=str(conv["id"]),
                session_id=conv["session_id"],
                mode=conv["mode"],
                status=conv["status"],
                title=conv["title"],
                duration=conv["duration"],
                performance_score=conv["performance_score"],
                difficulty_level=conv["difficulty_level"],
                created_at=conv["created_at"],
                completed_at=conv["completed_at"]
            )
            for conv in conversations
        ]
        
    except Exception as e:
        logger.error(f"Error getting user conversations: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@user_router.post("/check-interview-limit")
async def check_interview_limit(clerk_user_id: str = Depends(get_clerk_user_id)) -> Dict[str, Any]:
    """Check if user can start a new interview"""
    try:
        result = clerk_user_service.can_start_interview(clerk_user_id)
        return result
        
    except Exception as e:
        logger.error(f"Error checking interview limit: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@user_router.post("/start-interview")
async def start_interview(clerk_user_id: str = Depends(get_clerk_user_id)) -> Dict[str, Any]:
    """Start a new interview and increment usage"""
    try:
        # Check if user can start interview
        limit_check = clerk_user_service.can_start_interview(clerk_user_id)
        
        if not limit_check.get('can_start', False):
            raise HTTPException(
                status_code=403,
                detail={
                    "message": limit_check.get('reason', 'Cannot start interview'),
                    "limit_info": limit_check
                }
            )
        
        # Increment usage
        success = clerk_user_service.increment_monthly_usage(clerk_user_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update usage")
        
        return {
            "status": "success",
            "message": "Interview started successfully",
            "usage_info": {
                "current_usage": limit_check.get('current_usage', 0) + 1,
                "limit": limit_check.get('limit'),
                "subscription_tier": limit_check.get('subscription_tier')
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting interview: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@user_router.post("/create-user")
async def create_user_manually(
    clerk_user_data: Dict[str, Any],
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Manually create user (for testing or when webhooks aren't working)
    
    This endpoint can be used during development or as a fallback
    """
    try:
        user = clerk_user_service.create_or_update_user(clerk_user_data)
        
        if user:
            return {
                "status": "success",
                "message": "User created successfully",
                "user": {
                    "id": user["id"],
                    "clerk_user_id": user["clerk_user_id"],
                    "email": user["email"],
                    "full_name": user["full_name"]
                }
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create user")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user manually: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Health check endpoint
@user_router.get("/health")
async def user_api_health():
    """Health check for user API"""
    return {
        "status": "healthy",
        "service": "user_api",
        "endpoints": [
            "/api/user/profile",
            "/api/user/stats",
            "/api/user/conversations",
            "/api/user/check-interview-limit",
            "/api/user/start-interview"
        ]
    } 