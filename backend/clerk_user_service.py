"""
Clerk User Service
Handles integration between Clerk authentication and Supabase user management
"""

import os
import logging
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClerkUserService:
    def __init__(self):
        """Initialize Supabase client for user management"""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        logger.info("ClerkUserService initialized successfully")

    def create_or_update_user(self, clerk_user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create or update user in Supabase based on Clerk user data
        
        Args:
            clerk_user_data: User data from Clerk webhook or API
            
        Returns:
            User record from Supabase or None if failed
        """
        try:
            clerk_user_id = clerk_user_data.get('id')
            email = None
            full_name = None
            
            # Extract email from email_addresses array
            email_addresses = clerk_user_data.get('email_addresses', [])
            if email_addresses:
                primary_email = next((e for e in email_addresses if e.get('primary')), email_addresses[0])
                email = primary_email.get('email_address')
            
            # Extract full name
            first_name = clerk_user_data.get('first_name', '')
            last_name = clerk_user_data.get('last_name', '')
            full_name = f"{first_name} {last_name}".strip()
            
            if not clerk_user_id or not email:
                logger.error("Missing required user data: clerk_user_id or email")
                return None
            
            # Check if user already exists
            existing_user = self.get_user_by_clerk_id(clerk_user_id)
            
            if existing_user:
                # Update existing user
                updated_user = self.update_user(clerk_user_id, {
                    'email': email,
                    'full_name': full_name,
                    'updated_at': datetime.utcnow().isoformat()
                })
                logger.info(f"Updated user: {clerk_user_id}")
                return updated_user
            else:
                # Create new user
                new_user = self.create_user(clerk_user_id, email, full_name)
                logger.info(f"Created new user: {clerk_user_id}")
                return new_user
                
        except Exception as e:
            logger.error(f"Error creating/updating user: {str(e)}")
            return None

    def create_user(self, clerk_user_id: str, email: str, full_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Create a new user in Supabase"""
        try:
            user_data = {
                'clerk_user_id': clerk_user_id,
                'email': email,
                'full_name': full_name,
                'experience_level': 'entry',  # Default
                'target_companies': [],
                'subscription_tier': 'free',   # Default
                'interviews_used_this_month': 0
            }
            
            result = self.supabase.table('users').insert(user_data).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return None

    def get_user_by_clerk_id(self, clerk_user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by Clerk user ID"""
        try:
            result = self.supabase.table('users').select('*').eq('clerk_user_id', clerk_user_id).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by Clerk ID: {str(e)}")
            return None

    def update_user(self, clerk_user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user data"""
        try:
            result = self.supabase.table('users').update(update_data).eq('clerk_user_id', clerk_user_id).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            return None

    def delete_user(self, clerk_user_id: str) -> bool:
        """Delete user and all related data"""
        try:
            # Get user first to get the UUID
            user = self.get_user_by_clerk_id(clerk_user_id)
            if not user:
                logger.warning(f"User not found for deletion: {clerk_user_id}")
                return False
            
            # Delete user (CASCADE will handle related data)
            result = self.supabase.table('users').delete().eq('clerk_user_id', clerk_user_id).execute()
            
            logger.info(f"Deleted user: {clerk_user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            return False

    def get_user_conversations(self, clerk_user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's recent conversations"""
        try:
            user = self.get_user_by_clerk_id(clerk_user_id)
            if not user:
                return []
            
            result = self.supabase.table('conversations').select('*').eq('user_id', user['id']).order('created_at', desc=True).limit(limit).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting user conversations: {str(e)}")
            return []

    def get_user_stats(self, clerk_user_id: str) -> Dict[str, Any]:
        """Get user interview statistics"""
        try:
            user = self.get_user_by_clerk_id(clerk_user_id)
            if not user:
                return {}
            
            # Get conversation stats
            conversations = self.supabase.table('conversations').select('status, performance_score, created_at').eq('user_id', user['id']).execute()
            
            total_interviews = len(conversations.data) if conversations.data else 0
            completed_interviews = len([c for c in conversations.data if c['status'] == 'completed']) if conversations.data else 0
            
            # Calculate average score for completed interviews
            completed_scores = [c['performance_score'] for c in conversations.data if c['status'] == 'completed' and c['performance_score'] is not None] if conversations.data else []
            avg_score = sum(completed_scores) / len(completed_scores) if completed_scores else 0
            
            # Calculate current streak (simplified - could be more sophisticated)
            current_streak = min(completed_interviews, 7)  # Max 7 days
            
            return {
                'total_interviews': total_interviews,
                'completed_interviews': completed_interviews,
                'average_score': round(avg_score, 1),
                'current_streak': current_streak,
                'subscription_tier': user.get('subscription_tier', 'free'),
                'interviews_used_this_month': user.get('interviews_used_this_month', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats: {str(e)}")
            return {}

    def increment_monthly_usage(self, clerk_user_id: str) -> bool:
        """Increment the user's monthly interview usage"""
        try:
            user = self.get_user_by_clerk_id(clerk_user_id)
            if not user:
                return False
            
            current_usage = user.get('interviews_used_this_month', 0)
            
            result = self.supabase.table('users').update({
                'interviews_used_this_month': current_usage + 1
            }).eq('clerk_user_id', clerk_user_id).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error incrementing usage: {str(e)}")
            return False

    def can_start_interview(self, clerk_user_id: str) -> Dict[str, Any]:
        """Check if user can start a new interview based on subscription limits"""
        try:
            user = self.get_user_by_clerk_id(clerk_user_id)
            if not user:
                return {'can_start': False, 'reason': 'User not found'}
            
            subscription_tier = user.get('subscription_tier', 'free')
            interviews_used = user.get('interviews_used_this_month', 0)
            
            # Define limits per tier
            limits = {
                'free': 3,
                'premium': float('inf'),  # Unlimited
                'enterprise': float('inf')  # Unlimited
            }
            
            limit = limits.get(subscription_tier, 3)
            
            if interviews_used >= limit:
                return {
                    'can_start': False,
                    'reason': f'Monthly limit reached ({interviews_used}/{limit})',
                    'current_usage': interviews_used,
                    'limit': limit,
                    'subscription_tier': subscription_tier
                }
            
            return {
                'can_start': True,
                'current_usage': interviews_used,
                'limit': limit,
                'subscription_tier': subscription_tier
            }
            
        except Exception as e:
            logger.error(f"Error checking interview limit: {str(e)}")
            return {'can_start': False, 'reason': 'System error'}

# Global instance
clerk_user_service = ClerkUserService() 