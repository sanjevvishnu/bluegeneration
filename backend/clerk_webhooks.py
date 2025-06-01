"""
Clerk Webhook Handlers
Handles webhook events from Clerk for user lifecycle management
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import JSONResponse
import hmac
import hashlib
from clerk_user_service import clerk_user_service

# Configure logging
logger = logging.getLogger(__name__)

# Create router for webhook endpoints
webhook_router = APIRouter(prefix="/webhooks", tags=["webhooks"])

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify Clerk webhook signature
    
    Args:
        payload: Raw request body
        signature: Clerk signature from headers
        secret: Webhook secret from environment
        
    Returns:
        True if signature is valid, False otherwise
    """
    if not secret:
        logger.warning("CLERK_WEBHOOK_SECRET not configured")
        return False
    
    try:
        # Clerk uses HMAC-SHA256
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Remove 'sha256=' prefix if present
        if signature.startswith('sha256='):
            signature = signature[7:]
        
        return hmac.compare_digest(expected_signature, signature)
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {str(e)}")
        return False

@webhook_router.post("/clerk")
async def handle_clerk_webhook(
    request: Request,
    svix_signature: Optional[str] = Header(None, alias="svix-signature"),
    svix_timestamp: Optional[str] = Header(None, alias="svix-timestamp"),
    svix_id: Optional[str] = Header(None, alias="svix-id")
):
    """
    Handle Clerk webhook events
    
    Processes user lifecycle events from Clerk and syncs with Supabase
    """
    try:
        # Get raw payload
        payload = await request.body()
        
        # Get webhook secret from environment
        webhook_secret = os.getenv("CLERK_WEBHOOK_SECRET")
        
        # Verify signature if secret is configured
        if webhook_secret and svix_signature:
            if not verify_webhook_signature(payload, svix_signature, webhook_secret):
                logger.warning("Invalid webhook signature")
                raise HTTPException(status_code=401, detail="Invalid signature")
        elif webhook_secret:
            logger.warning("Webhook secret configured but no signature provided")
            raise HTTPException(status_code=401, detail="Missing signature")
        
        # Parse JSON payload
        try:
            data = json.loads(payload.decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON payload: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid JSON")
        
        # Get event type and data
        event_type = data.get('type')
        user_data = data.get('data', {})
        
        logger.info(f"Received Clerk webhook: {event_type}")
        
        # Handle different event types
        if event_type == 'user.created':
            result = await handle_user_created(user_data)
        elif event_type == 'user.updated':
            result = await handle_user_updated(user_data)
        elif event_type == 'user.deleted':
            result = await handle_user_deleted(user_data)
        else:
            logger.info(f"Unhandled event type: {event_type}")
            result = {"status": "ignored", "event_type": event_type}
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Clerk webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def handle_user_created(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle user creation event from Clerk"""
    try:
        logger.info(f"Creating user: {user_data.get('id')}")
        
        # Create user in Supabase
        user = clerk_user_service.create_or_update_user(user_data)
        
        if user:
            logger.info(f"Successfully created user: {user['clerk_user_id']}")
            return {
                "status": "success",
                "action": "user_created",
                "user_id": user['id'],
                "clerk_user_id": user['clerk_user_id']
            }
        else:
            logger.error("Failed to create user in Supabase")
            return {
                "status": "error",
                "action": "user_created",
                "message": "Failed to create user"
            }
            
    except Exception as e:
        logger.error(f"Error handling user creation: {str(e)}")
        return {
            "status": "error",
            "action": "user_created",
            "message": str(e)
        }

async def handle_user_updated(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle user update event from Clerk"""
    try:
        clerk_user_id = user_data.get('id')
        logger.info(f"Updating user: {clerk_user_id}")
        
        # Update user in Supabase
        user = clerk_user_service.create_or_update_user(user_data)
        
        if user:
            logger.info(f"Successfully updated user: {user['clerk_user_id']}")
            return {
                "status": "success",
                "action": "user_updated",
                "user_id": user['id'],
                "clerk_user_id": user['clerk_user_id']
            }
        else:
            logger.error("Failed to update user in Supabase")
            return {
                "status": "error",
                "action": "user_updated",
                "message": "Failed to update user"
            }
            
    except Exception as e:
        logger.error(f"Error handling user update: {str(e)}")
        return {
            "status": "error",
            "action": "user_updated",
            "message": str(e)
        }

async def handle_user_deleted(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle user deletion event from Clerk"""
    try:
        clerk_user_id = user_data.get('id')
        logger.info(f"Deleting user: {clerk_user_id}")
        
        # Delete user from Supabase
        success = clerk_user_service.delete_user(clerk_user_id)
        
        if success:
            logger.info(f"Successfully deleted user: {clerk_user_id}")
            return {
                "status": "success",
                "action": "user_deleted",
                "clerk_user_id": clerk_user_id
            }
        else:
            logger.warning(f"User not found for deletion: {clerk_user_id}")
            return {
                "status": "warning",
                "action": "user_deleted",
                "message": "User not found"
            }
            
    except Exception as e:
        logger.error(f"Error handling user deletion: {str(e)}")
        return {
            "status": "error",
            "action": "user_deleted",
            "message": str(e)
        }

# Health check endpoint for webhooks
@webhook_router.get("/health")
async def webhook_health():
    """Health check for webhook service"""
    return {
        "status": "healthy",
        "service": "clerk_webhooks",
        "webhook_secret_configured": bool(os.getenv("CLERK_WEBHOOK_SECRET"))
    } 