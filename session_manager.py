#!/usr/bin/env python3
"""
Session Manager for Live Audio Interview Practice
Handles session lifecycle, state management, and coordination
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from dataclasses import asdict

from config import config
from models import SessionInfo, SessionMode, ResponseModality, TranscriptEntry, InterviewPrompts

class SessionManager:
    """
    Manages interview sessions, their state, and lifecycle
    Coordinates between different components
    """
    
    def __init__(self):
        self.active_sessions: Dict[str, SessionInfo] = {}
        self.session_locks: Dict[str, asyncio.Lock] = {}
        self.prompts: InterviewPrompts = self._load_prompts()
        self.cleanup_task = None
        self._cleanup_started = False
        
        # Don't start cleanup task here - will be started lazily when event loop is available
    
    def _load_prompts(self) -> InterviewPrompts:
        """Load interview prompts from prompts.json"""
        try:
            with open('prompts.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("❌ prompts.json file not found. Using default prompts.")
            return {
                "amazon_interviewer": {
                    "name": "Amazon Technical Interviewer",
                    "system_instruction": "You are a senior software engineer and interviewer at Amazon. You are conducting a technical interview for a software engineering position. Be professional, friendly but thorough.",
                    "welcome_message": "🚀 Amazon Interview Mode",
                    "description": "📦 Amazon Interview Mode: Technical + Leadership Principles"
                }
            }
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing prompts.json: {e}")
            return {}
    
    async def create_session(self, session_id: str, mode: str, response_modality: ResponseModality = ResponseModality.TEXT, use_elevenlabs: bool = False) -> Optional[SessionInfo]:
        """Create a new interview session"""
        # Start cleanup task if not already started
        self._ensure_cleanup_task_started()
        
        try:
            # Validate mode
            if mode not in self.prompts:
                print(f"❌ Invalid interview mode: {mode}")
                return None
            
            # Get system instruction from prompts
            prompt_config = self.prompts[mode]
            system_instruction = prompt_config.get('system_instruction', 'You are a helpful assistant.')
            
            # Create session info
            session_info = SessionInfo(
                session_id=session_id,
                mode=SessionMode(mode),
                response_modality=response_modality,
                use_elevenlabs=use_elevenlabs,
                system_instruction=system_instruction
            )
            
            # Store session
            self.active_sessions[session_id] = session_info
            self.session_locks[session_id] = asyncio.Lock()
            
            print(f"✅ Created session {session_id} (mode: {mode}, modality: {response_modality.value})")
            return session_info
            
        except Exception as e:
            print(f"❌ Failed to create session {session_id}: {e}")
            return None
    
    async def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """Get session information"""
        return self.active_sessions.get(session_id)
    
    async def update_session_mode(self, session_id: str, new_mode: str) -> bool:
        """Update session interview mode"""
        if session_id not in self.active_sessions:
            return False
        
        if new_mode not in self.prompts:
            print(f"❌ Invalid interview mode: {new_mode}")
            return False
        
        try:
            session = self.active_sessions[session_id]
            session.mode = SessionMode(new_mode)
            session.system_instruction = self.prompts[new_mode].get('system_instruction', 'You are a helpful assistant.')
            
            print(f"✅ Updated session {session_id} mode to {new_mode}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update session mode: {e}")
            return False
    
    async def update_voice_settings(self, session_id: str, use_elevenlabs: bool) -> bool:
        """Update session voice settings"""
        if session_id not in self.active_sessions:
            return False
        
        try:
            session = self.active_sessions[session_id]
            session.use_elevenlabs = use_elevenlabs
            
            print(f"✅ Updated session {session_id} voice settings (ElevenLabs: {use_elevenlabs})")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update voice settings: {e}")
            return False
    
    async def switch_response_modality(self, session_id: str, new_modality: ResponseModality) -> bool:
        """
        Switch session response modality
        Note: This may require recreating Gemini Live API sessions
        """
        if session_id not in self.active_sessions:
            return False
        
        try:
            session = self.active_sessions[session_id]
            old_modality = session.response_modality
            session.response_modality = new_modality
            
            print(f"✅ Switched session {session_id} modality: {old_modality.value} -> {new_modality.value}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to switch response modality: {e}")
            return False
    
    async def get_session_lock(self, session_id: str) -> Optional[asyncio.Lock]:
        """Get session lock for thread-safe operations"""
        return self.session_locks.get(session_id)
    
    async def close_session(self, session_id: str) -> bool:
        """Close and clean up session"""
        try:
            # Remove from active sessions
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            # Remove lock
            if session_id in self.session_locks:
                del self.session_locks[session_id]
            
            print(f"✅ Closed session {session_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error closing session {session_id}: {e}")
            return False
    
    def list_active_sessions(self) -> List[str]:
        """Get list of active session IDs"""
        return list(self.active_sessions.keys())
    
    def get_session_count(self) -> int:
        """Get count of active sessions"""
        return len(self.active_sessions)
    
    def get_prompts(self) -> InterviewPrompts:
        """Get available interview prompts"""
        return self.prompts
    
    def get_session_stats(self) -> Dict:
        """Get session statistics"""
        now = datetime.now()
        stats = {
            "total_sessions": len(self.active_sessions),
            "sessions_by_mode": {},
            "sessions_by_modality": {},
            "oldest_session": None,
            "newest_session": None
        }
        
        if self.active_sessions:
            # Group by mode
            for session in self.active_sessions.values():
                mode = session.mode.value
                modality = session.response_modality.value
                
                stats["sessions_by_mode"][mode] = stats["sessions_by_mode"].get(mode, 0) + 1
                stats["sessions_by_modality"][modality] = stats["sessions_by_modality"].get(modality, 0) + 1
            
            # Find oldest and newest
            sessions_by_time = sorted(self.active_sessions.values(), key=lambda s: s.created_at)
            stats["oldest_session"] = {
                "session_id": sessions_by_time[0].session_id,
                "age_minutes": (now - sessions_by_time[0].created_at).total_seconds() / 60
            }
            stats["newest_session"] = {
                "session_id": sessions_by_time[-1].session_id,
                "age_minutes": (now - sessions_by_time[-1].created_at).total_seconds() / 60
            }
        
        return stats
    
    def _start_cleanup_task(self):
        """Start background cleanup task"""
        async def cleanup_expired_sessions():
            while True:
                try:
                    await asyncio.sleep(300)  # Check every 5 minutes
                    await self._cleanup_expired_sessions()
                except Exception as e:
                    print(f"❌ Error in cleanup task: {e}")
        
        self.cleanup_task = asyncio.create_task(cleanup_expired_sessions())
    
    async def _cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        now = datetime.now()
        max_duration = timedelta(seconds=config.MAX_SESSION_DURATION)
        
        expired_sessions = []
        
        for session_id, session in self.active_sessions.items():
            if now - session.created_at > max_duration:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            print(f"🧹 Cleaning up expired session: {session_id}")
            await self.close_session(session_id)
        
        if expired_sessions:
            print(f"🧹 Cleaned up {len(expired_sessions)} expired sessions")
    
    async def shutdown(self):
        """Shutdown session manager"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            
        # Close all active sessions
        session_ids = list(self.active_sessions.keys())
        for session_id in session_ids:
            await self.close_session(session_id)
        
        print("✅ Session manager shutdown complete")
    
    def _ensure_cleanup_task_started(self):
        """Ensure cleanup task is started (lazy initialization)"""
        if not self._cleanup_started:
            try:
                self._start_cleanup_task()
                self._cleanup_started = True
            except RuntimeError:
                # No event loop available yet, will try again later
                pass 