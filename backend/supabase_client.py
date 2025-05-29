#!/usr/bin/env python3
"""
Supabase Client for Live Audio Interview Practice
Handles database operations and real-time subscriptions
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from supabase import create_client, Client

from config import config
from models import SessionInfo, TranscriptEntry

class SupabaseClient:
    """
    Dedicated Supabase client for database operations
    Handles sessions, transcripts, and real-time updates
    """
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.is_connected = False
        self.initialize_client()
    
    def initialize_client(self):
        """Initialize Supabase client"""
        if not config.SUPABASE_URL or not config.SUPABASE_ANON_KEY:
            print("❌ Supabase configuration missing")
            print("📝 Set SUPABASE_URL and SUPABASE_ANON_KEY in .env file")
            return
        
        try:
            self.client = create_client(config.SUPABASE_URL, config.SUPABASE_ANON_KEY)
            self.is_connected = True
            print("✅ Supabase client initialized")
        except Exception as e:
            print(f"❌ Failed to initialize Supabase client: {e}")
            self.client = None
            self.is_connected = False
    
    @property
    def is_available(self) -> bool:
        """Check if Supabase client is available"""
        return self.client is not None and self.is_connected
    
    async def create_session_record(self, session_info: SessionInfo) -> Optional[Dict]:
        """Create a session record in the database"""
        if not self.is_available:
            return None
        
        try:
            session_data = {
                'session_id': session_info.session_id,
                'mode': session_info.mode.value,
                'use_elevenlabs': session_info.use_elevenlabs,
                'status': 'active'
            }
            
            result = self.client.table('interview_sessions').insert(session_data).execute()
            
            if result.data:
                print(f"✅ Created session record for {session_info.session_id}")
                return result.data[0]
            else:
                print(f"❌ Failed to create session record: {result}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating session record: {e}")
            return None
    
    async def update_session_status(self, session_id: str, status: str) -> bool:
        """Update session status"""
        if not self.is_available:
            return False
        
        try:
            result = self.client.table('interview_sessions').update({
                'status': status,
                'updated_at': datetime.now().isoformat()
            }).eq('session_id', session_id).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            print(f"❌ Error updating session status: {e}")
            return False
    
    async def update_session_mode(self, session_id: str, mode: str) -> bool:
        """Update session interview mode"""
        if not self.is_available:
            return False
        
        try:
            result = self.client.table('interview_sessions').update({
                'mode': mode,
                'updated_at': datetime.now().isoformat()
            }).eq('session_id', session_id).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            print(f"❌ Error updating session mode: {e}")
            return False
    
    async def add_transcript_entry(self, transcript: TranscriptEntry) -> Optional[Dict]:
        """Add a transcript entry to the database"""
        if not self.is_available:
            return None
        
        try:
            transcript_data = {
                'session_id': transcript.session_id,
                'speaker': transcript.speaker,
                'text': transcript.text,
                'provider': transcript.provider,
                'timestamp': transcript.timestamp.isoformat()
            }
            
            result = self.client.table('transcripts').insert(transcript_data).execute()
            
            if result.data:
                return result.data[0]
            else:
                print(f"❌ Failed to add transcript entry: {result}")
                return None
                
        except Exception as e:
            print(f"❌ Error adding transcript entry: {e}")
            return None
    
    async def get_conversation_history(self, session_id: str, limit: int = 20) -> List[Dict]:
        """Get conversation history for a session"""
        if not self.is_available:
            return []
        
        try:
            result = self.client.table('transcripts').select(
                'speaker, text, provider, timestamp'
            ).eq('session_id', session_id).order('timestamp').limit(limit).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"❌ Error getting conversation history: {e}")
            return []
    
    async def get_full_transcript(self, session_id: str) -> Dict:
        """Get full transcript for a session"""
        if not self.is_available:
            return {"session_id": session_id, "transcript": []}
        
        try:
            result = self.client.table('transcripts').select('*').eq(
                'session_id', session_id
            ).order('timestamp').execute()
            
            return {
                "session_id": session_id,
                "transcript": result.data if result.data else []
            }
            
        except Exception as e:
            print(f"❌ Error getting full transcript: {e}")
            return {"session_id": session_id, "transcript": []}
    
    async def delete_session_data(self, session_id: str) -> bool:
        """Delete all data for a session"""
        if not self.is_available:
            return False
        
        try:
            # Delete transcripts first (foreign key constraint)
            transcript_result = self.client.table('transcripts').delete().eq(
                'session_id', session_id
            ).execute()
            
            # Delete session record
            session_result = self.client.table('interview_sessions').delete().eq(
                'session_id', session_id
            ).execute()
            
            print(f"✅ Deleted session data for {session_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting session data: {e}")
            return False
    
    async def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get session information from database"""
        if not self.is_available:
            return None
        
        try:
            result = self.client.table('interview_sessions').select('*').eq(
                'session_id', session_id
            ).single().execute()
            
            return result.data if result.data else None
            
        except Exception as e:
            print(f"❌ Error getting session info: {e}")
            return None
    
    async def get_active_sessions(self) -> List[Dict]:
        """Get all active sessions"""
        if not self.is_available:
            return []
        
        try:
            result = self.client.table('interview_sessions').select('*').eq(
                'status', 'active'
            ).order('created_at', desc=True).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"❌ Error getting active sessions: {e}")
            return []
    
    async def cleanup_old_sessions(self, hours_old: int = 24) -> int:
        """Clean up old sessions"""
        if not self.is_available:
            return 0
        
        try:
            # Calculate cutoff time
            cutoff = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_iso = cutoff.isoformat()
            
            # Get old sessions
            old_sessions = self.client.table('interview_sessions').select(
                'session_id'
            ).lt('created_at', cutoff_iso).execute()
            
            if not old_sessions.data:
                return 0
            
            session_ids = [s['session_id'] for s in old_sessions.data]
            
            # Delete transcripts for old sessions
            for session_id in session_ids:
                await self.delete_session_data(session_id)
            
            print(f"🧹 Cleaned up {len(session_ids)} old sessions")
            return len(session_ids)
            
        except Exception as e:
            print(f"❌ Error cleaning up old sessions: {e}")
            return 0
    
    async def get_database_stats(self) -> Dict:
        """Get database statistics"""
        if not self.is_available:
            return {"error": "Database not available"}
        
        try:
            # Count sessions
            sessions_result = self.client.table('interview_sessions').select(
                'id', count='exact'
            ).execute()
            
            # Count transcripts
            transcripts_result = self.client.table('transcripts').select(
                'id', count='exact'
            ).execute()
            
            # Get active sessions
            active_sessions = await self.get_active_sessions()
            
            return {
                "total_sessions": sessions_result.count,
                "total_transcripts": transcripts_result.count,
                "active_sessions": len(active_sessions),
                "database_connected": True
            }
            
        except Exception as e:
            print(f"❌ Error getting database stats: {e}")
            return {
                "error": str(e),
                "database_connected": False
            }
    
    def subscribe_to_transcripts(self, session_id: str, callback):
        """
        Subscribe to real-time transcript updates
        Note: This is a synchronous method for Supabase real-time subscriptions
        """
        if not self.is_available:
            return None
        
        try:
            # Supabase real-time subscription
            subscription = self.client.table('transcripts').on('INSERT').filter(
                'session_id', 'eq', session_id
            ).subscribe(callback)
            
            return subscription
            
        except Exception as e:
            print(f"❌ Error subscribing to transcripts: {e}")
            return None
    
    async def test_connection(self) -> Dict:
        """Test database connection and permissions"""
        if not self.is_available:
            return {"connected": False, "error": "Client not initialized"}
        
        try:
            # Test basic query
            result = self.client.table('interview_sessions').select('id').limit(1).execute()
            
            return {
                "connected": True,
                "tables_accessible": True,
                "message": "Database connection successful"
            }
            
        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
                "message": "Database connection failed"
            } 