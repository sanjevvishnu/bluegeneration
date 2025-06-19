#!/usr/bin/env python3
"""
Simplified Supabase Backend for Coimbatore
Uses FastAPI + Supabase with just conversations and transcripts tables
Integrates Gemini Live API
"""

import os
import asyncio
import json
import base64
import traceback
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import tempfile
import wave
import numpy as np
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# FastAPI and web framework imports
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

# Supabase imports
from supabase import create_client, Client

# Audio and AI imports
import aiohttp
import websockets
from google.genai.types import LiveConnectConfig, Blob

# Load environment variables (check parent directory first, then local)
load_dotenv(dotenv_path="../.env")  # Parent directory
load_dotenv()  # Local backend/.env (if exists, overrides parent)

# Gemini imports
try:
    from google import genai
    from google.genai.types import LiveConnectConfig, Blob
    GEMINI_AVAILABLE = True
except ImportError:
    print("❌ Warning: Google Gemini SDK not installed. Install with: pip install google-genai")
    GEMINI_AVAILABLE = False

# Import Clerk integration modules
from conversation_integration import conversation_integrator
try:
    from clerk_webhooks import webhook_router
    from user_api import user_router
    from clerk_user_service import ClerkUserService
    CLERK_INTEGRATION_AVAILABLE = True
    print("✅ Clerk integration modules loaded")
except ImportError as e:
    print(f"❌ Warning: Clerk integration not available: {e}")
    CLERK_INTEGRATION_AVAILABLE = False

class SimpleSupabaseBackend:
    def __init__(self):
        # Environment variables
        self.gemini_api_key = os.getenv('GOOGLE_API_KEY')
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')  # Use service role key to bypass RLS
        
        # Initialize Supabase client
        if not self.supabase_url or not self.supabase_key:
            print("❌ SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env file")
            print("📝 Get these from: https://supabase.com/dashboard/project/[project-id]/settings/api")
            self.supabase = None
        else:
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
            print("✅ Supabase client initialized with Service Role Key (bypasses RLS)")
        
        # Initialize Gemini client
        self.gemini_client = None
        if GEMINI_AVAILABLE and self.gemini_api_key and self.gemini_api_key != 'your_google_api_key_here':
            try:
                self.gemini_client = genai.Client(api_key=self.gemini_api_key)
                print("✅ Gemini client initialized")
            except Exception as e:
                print(f"❌ Failed to initialize Gemini: {e}")
        
        # Configuration
        self.model_name = "models/gemini-2.0-flash-live-001"
        self.sample_rate = 16000
        self.channels = 1
        
        # Active sessions and WebSocket connections
        self.active_sessions: Dict[str, Any] = {}
        self.websocket_connections: Dict[str, WebSocket] = {}
        self.gemini_sessions: Dict[str, Any] = {}
        
        # Audio streaming queues for each session
        self.audio_out_queues: Dict[str, asyncio.Queue] = {}
        self.audio_streaming_tasks: Dict[str, asyncio.Task] = {}
        
        # Transcript accumulation for complete responses
        self.transcript_buffers: Dict[str, Dict[str, str]] = {}  # session_id -> {speaker: accumulated_text}
        
        # Transcript timing for buffer management
        self.transcript_timers: Dict[str, Dict[str, Any]] = {}  # session_id -> {speaker: timer_info}
        
        # Load interview prompts
        self.prompts = self.load_prompts()
        
        # Initialize Clerk User Service if available
        if CLERK_INTEGRATION_AVAILABLE:
            try:
                self.clerk_user_service = ClerkUserService()
                print("✅ Clerk User Service initialized")
            except Exception as e:
                print(f"❌ Failed to initialize Clerk User Service: {e}")
                self.clerk_user_service = None
        else:
            self.clerk_user_service = None
        
        print(f"🐍 Simple Supabase Backend initializing...")
        print(f"🗄️ Supabase: {'✅ Connected' if self.supabase else '❌ Not configured'}")
        
    def load_prompts(self):
        """Load interview prompts from prompts.json file"""
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
    
    async def create_conversation(self, session_id: str, mode: str, user_id: str = None):
        """Create a new conversation with optional user association"""
        if not self.supabase:
            print(f"❌ Supabase client not available for session {session_id}")
            return None
            
        try:
            print(f"🔍 Creating conversation for session {session_id} with mode {mode}")
            
            # Check if conversation already exists
            existing = self.supabase.table('conversations').select('*').eq('session_id', session_id).execute()
            if existing.data:
                print(f"✅ Conversation {session_id} already exists")
                return existing.data[0]
            
            # Prepare conversation data
            conversation_data = {
                'session_id': session_id,
                'mode': mode,
                'status': 'active',
                'title': f"{mode} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            }
            
            # Handle user_id if provided (Clerk user ID needs to be converted to UUID)
            if user_id:
                print(f"🔗 Looking up user with Clerk ID: {user_id}")
                
                # Look up the user by clerk_user_id to get their UUID
                user_query = self.supabase.table('users').select('id').eq('clerk_user_id', user_id).execute()
                
                if user_query.data:
                    user_uuid = user_query.data[0]['id']
                    conversation_data['user_id'] = user_uuid
                    print(f"✅ Found user UUID: {user_uuid} for Clerk ID: {user_id}")
                else:
                    print(f"❌ User not found with Clerk ID: {user_id}")
                    print("🚫 Conversation creation failed - user must exist in database")
                    return None
            else:
                print("❌ No user_id provided")
                print("🚫 Conversation creation failed - user authentication required")
                return None
            
            print(f"📝 Inserting conversation data: {conversation_data}")
            
            # Create new conversation
            result = self.supabase.table('conversations').insert(conversation_data).execute()
            
            if result.data:
                print(f"✅ Created conversation {session_id} in database with ID: {result.data[0]['id']}")
                
                # Verify the creation by reading it back
                verification = self.supabase.table('conversations').select('*').eq('session_id', session_id).execute()
                if verification.data:
                    print(f"✅ Verified conversation exists in database")
                else:
                    print(f"⚠️ Warning: Conversation created but verification failed")
                
                return result.data[0]
            else:
                print(f"❌ No data returned from conversation creation")
                return None
            
        except Exception as e:
            print(f"❌ Failed to create conversation: {e}")
            print(f"🔍 Exception type: {type(e)}")
            import traceback
            print(f"🔍 Full traceback: {traceback.format_exc()}")
            return None
    
    async def add_transcript(self, session_id: str, speaker: str, text: str, provider: str = None, confidence_score: float = None, user_id: str = None):
        """Add a transcript entry with optional user association"""
        if not self.supabase:
            return None
            
        try:
            # Get conversation ID from session_id
            conversation = self.supabase.table('conversations').select('id, user_id').eq('session_id', session_id).execute()
            
            if not conversation.data:
                return None
            
            conversation_id = conversation.data[0]['id']
            conversation_user_id = conversation.data[0].get('user_id')
            
            # Prepare transcript data
            transcript_data = {
                'conversation_id': conversation_id,
                'session_id': session_id,
                'speaker': speaker,
                'text': text,
                'provider': provider or 'unknown',
                'confidence_score': confidence_score
            }
            
            # Handle user_id conversion (Clerk user ID to UUID)
            final_user_id = None
            
            if user_id:
                # Check if this looks like a Clerk user ID (starts with "user_")
                if user_id.startswith('user_'):
                    # Look up the user by clerk_user_id to get their UUID
                    user_query = self.supabase.table('users').select('id').eq('clerk_user_id', user_id).execute()
                    
                    if user_query.data:
                        final_user_id = user_query.data[0]['id']
                    else:
                        pass
                else:
                    # Assume it's already a UUID
                    final_user_id = user_id
            elif conversation_user_id:
                final_user_id = conversation_user_id
            
            if final_user_id:
                transcript_data['user_id'] = final_user_id
            
            result = self.supabase.table('transcripts').insert(transcript_data).execute()
            
            if result.data:
                return result.data[0]
            else:
                return None
            
        except Exception as e:
            print(f"❌ Failed to add transcript: {e}")
            return None
    
    async def get_conversation_transcripts(self, session_id: str, limit: int = 100):
        """Get all transcripts for a conversation"""
        if not self.supabase:
            return []
            
        try:
            result = self.supabase.table('transcripts').select('*').eq('session_id', session_id).order('sequence_number').limit(limit).execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"❌ Failed to get transcripts: {e}")
            return []
    
    async def update_conversation_status(self, session_id: str, status: str, duration: int = None):
        """Update conversation status and duration"""
        if not self.supabase:
            return None
            
        try:
            update_data = {'status': status, 'updated_at': datetime.now().isoformat()}
            if duration is not None:
                update_data['duration'] = duration
            if status == 'completed':
                update_data['completed_at'] = datetime.now().isoformat()
            
            result = self.supabase.table('conversations').update(update_data).eq('session_id', session_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"❌ Failed to update conversation: {e}")
            return None
    
    async def create_gemini_session(self, session_id: str, system_instruction: str):
        """Create a Gemini Live session with audio and transcription enabled"""
        if not self.gemini_client:
            return None
            
        try:
            # Enhanced configuration with audio and transcription
            config = LiveConnectConfig(
                response_modalities=["AUDIO"],
                input_audio_transcription={},    # Enable user speech transcription
                output_audio_transcription={},   # Enable AI speech transcription
                system_instruction=system_instruction + """

IMPORTANT REAL-TIME CONVERSATION RULES:
1. You MUST respond with AUDIO speech, not text
2. Listen carefully to what the user says and respond directly to their input
3. Keep your responses conversational and natural (2-3 sentences max)
4. Be interactive and responsive - this is a real-time voice conversation
5. Acknowledge what the user said before asking new questions
6. Speak clearly and at a normal pace
7. Keep responses concise to allow for natural turn-taking
8. Be prepared to be interrupted at any time - this is normal in conversation

Remember: This is a real-time voice conversation with full transcription enabled."""
            )
            
            # Create the context manager but don't enter it yet
            session_cm = self.gemini_client.aio.live.connect(
                model=self.model_name,
                config=config
            )
            
            # Enter the context manager to get the actual session
            session = await session_cm.__aenter__()
            
            # Store both the session and context manager for proper cleanup
            self.gemini_sessions[session_id] = {
                'session': session,
                'context_manager': session_cm
            }
            
            print(f"✅ Created Gemini session with enhanced transcription for {session_id}")
            return session
            
        except Exception as e:
            print(f"❌ Failed to create session: {e}")
            traceback.print_exc()
            return None
    
    async def close_session(self, session_id: str):
        """Close a session and cleanup"""
        # Stop audio streaming tasks
        if session_id in self.audio_streaming_tasks:
            task = self.audio_streaming_tasks[session_id]
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            del self.audio_streaming_tasks[session_id]
        
        # Cleanup audio queue
        if session_id in self.audio_out_queues:
            queue = self.audio_out_queues[session_id]
            # Send shutdown signal
            await queue.put(None)
            del self.audio_out_queues[session_id]
        
        # Close Gemini session properly
        if session_id in self.gemini_sessions:
            try:
                session_info = self.gemini_sessions[session_id]
                context_manager = session_info['context_manager']
                
                # Properly exit the context manager
                await context_manager.__aexit__(None, None, None)
                
                del self.gemini_sessions[session_id]
            except Exception as e:
                print(f"❌ Error closing session: {e}")
        
        # Remove from active sessions
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            print(f"✅ Removed session {session_id} from active sessions")
        
        # Clean up transcript buffers and timers
        if session_id in self.transcript_buffers:
            # Cancel any pending timers
            if session_id in self.transcript_timers:
                for speaker_timers in self.transcript_timers[session_id].values():
                    if speaker_timers.get('timer'):
                        speaker_timers['timer'].cancel()
                del self.transcript_timers[session_id]
            
            # Save any remaining buffered text
            for speaker, buffered_text in self.transcript_buffers[session_id].items():
                if buffered_text.strip():
                    await self.add_transcript(session_id, speaker, buffered_text.strip(), "session_cleanup")
                    print(f"📝 {speaker.title()}: {buffered_text.strip()}")
            
            del self.transcript_buffers[session_id]
        
        # Remove WebSocket connection
        if session_id in self.websocket_connections:
            del self.websocket_connections[session_id]
        
        # Clean up conversation flow state
        try:
            await conversation_integrator.handle_session_end(session_id)
            print(f"🎯 Conversation flow cleanup completed for session {session_id}")
        except Exception as e:
            print(f"❌ Error cleaning up conversation flow: {e}")

    async def process_user_message_with_flow(self, session_id: str, user_text: str):
        """Process user message through conversation flow and inject guidance if needed"""
        try:
            # Process user message through conversation integrator
            flow_result = await conversation_integrator.process_user_message(session_id, user_text)
            
            if flow_result and flow_result.get('should_inject_context'):
                context_injection = flow_result.get('context_injection', '')
                
                # Send context injection to Gemini session
                if session_id in self.gemini_sessions and context_injection:
                    session_info = self.gemini_sessions[session_id]
                    session = session_info['session']
                    
                    print(f"🎯 Injecting conversation guidance for session {session_id}")
                    print(f"📋 Guidance preview: {context_injection[:100]}...")
                    
                    # Send context injection as a system message to guide the next AI response
                    await session.send_text(context_injection)
                    
        except Exception as e:
            print(f"❌ Error processing user message with conversation flow: {e}")
            # Don't let conversation flow errors break the main conversation
            pass

    async def start_audio_streaming(self, session_id: str, websocket: WebSocket):
        """Start background audio streaming for a session"""
        if session_id not in self.gemini_sessions:
            return
            
        # Create audio queue for this session
        self.audio_out_queues[session_id] = asyncio.Queue()
        
        # Start background tasks for audio streaming
        receive_task = asyncio.create_task(self.receive_audio_from_gemini(session_id))
        send_task = asyncio.create_task(self.send_audio_to_websocket(session_id, websocket))
        
        # Store tasks for cleanup
        self.audio_streaming_tasks[session_id] = receive_task
        
    async def receive_audio_from_gemini(self, session_id: str):
        """Continuously receive audio and transcripts from Gemini Live API"""
        if session_id not in self.gemini_sessions:
            return
            
        session_info = self.gemini_sessions[session_id]
        session = session_info['session']
        
        # Get user_id from active session
        session_state = self.active_sessions.get(session_id, {})
        user_id = session_state.get('user_id')
        
        try:
            while session_id in self.gemini_sessions:
                turn = session.receive()
                
                async for response in turn:
                    # Handle audio data
                    if response.data:
                        # Queue audio data for WebSocket sending
                        if session_id in self.audio_out_queues:
                            await self.audio_out_queues[session_id].put(response.data)
                    
                    # Handle transcripts using official Gemini Live API structure
                    transcript_found = False
                    
                    # Check for server_content (official API structure)
                    if hasattr(response, 'server_content') and response.server_content:
                        server_content = response.server_content
                        
                        # Handle AI output transcription (AI speech-to-text)
                        if hasattr(server_content, 'output_transcription') and server_content.output_transcription:
                            if hasattr(server_content.output_transcription, 'text') and server_content.output_transcription.text:
                                ai_transcript = server_content.output_transcription.text
                                await self.add_buffered_transcript(session_id, "assistant", ai_transcript, "gemini_live_output_transcription", user_id=user_id)
                                transcript_found = True
                        
                        # Handle user input transcription (user speech-to-text)
                        if hasattr(server_content, 'input_transcription') and server_content.input_transcription:
                            if hasattr(server_content.input_transcription, 'text') and server_content.input_transcription.text:
                                user_transcript = server_content.input_transcription.text
                                await self.add_buffered_transcript(session_id, "user", user_transcript, "gemini_live_input_transcription", user_id=user_id)
                                transcript_found = True
                                
                                # Process user message through conversation flow
                                await self.process_user_message_with_flow(session_id, user_transcript)
                        
                        # Handle model turn content (for text responses)
                        if hasattr(server_content, 'model_turn') and server_content.model_turn:
                            model_turn = server_content.model_turn
                            
                            # Check if model_turn has parts with text
                            if hasattr(model_turn, 'parts') and model_turn.parts:
                                for part in model_turn.parts:
                                    if hasattr(part, 'text') and part.text:
                                        await self.add_buffered_transcript(session_id, "assistant", part.text, "gemini_live_model_turn", user_id=user_id)
                                        transcript_found = True
                    
                    # Fallback: Check direct response.text (legacy support)
                    if not transcript_found and response.text:
                        await self.add_buffered_transcript(session_id, "assistant", response.text, "gemini_live_direct_text", user_id=user_id)
                    
        except Exception as e:
            print(f"❌ Error receiving audio for session {session_id}: {e}")
            traceback.print_exc()
    
    async def send_audio_to_websocket(self, session_id: str, websocket: WebSocket):
        """Send audio from queue to WebSocket client"""
        if session_id not in self.audio_out_queues:
            return
            
        audio_queue = self.audio_out_queues[session_id]
        
        try:
            while True:
                # Get audio data from queue (wait for it)
                audio_data = await audio_queue.get()
                
                if audio_data is None:  # Shutdown signal
                    break
                    
                # Convert to base64 and send to WebSocket
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                
                await websocket.send_json({
                    'type': 'audio_response',
                    'data': {
                        'audio': audio_base64,
                        'format': 'pcm',  # Raw PCM audio from Gemini
                        'sample_rate': 24000,  # Gemini outputs at 24kHz
                        'channels': 1
                    }
                })
                
                # Mark task as done
                audio_queue.task_done()
                
        except Exception as e:
            print(f"❌ Error sending audio to WebSocket for session {session_id}: {e}")
            traceback.print_exc()

    async def handle_websocket_message(self, websocket: WebSocket, session_id: str, message: Dict):
        async def send_if_open(data: Dict):
            """Helper function to send data only if WebSocket is still open"""
            try:
                await websocket.send_json(data)
            except Exception as e:
                # Silently ignore WebSocket send errors - this is expected when connection is closed
                pass
        
        try:
            message_type = message.get('type')
            data = message.get('data', {})
            
            if message_type == 'create_session':
                mode = data.get('mode', 'amazon_interviewer')
                user_id = data.get('user_id')  # Extract user_id from Clerk frontend
                
                print(f"🚀 Creating session {session_id} with mode {mode}")
                if user_id:
                    print(f"🔗 User authenticated: {user_id}")
                else:
                    print("❌ No user_id provided - authentication required")
                
                # Create conversation in database with user_id
                conversation = await self.create_conversation(session_id, mode, user_id)
                
                if not conversation:
                    print(f"❌ Failed to create conversation for session {session_id}")
                    
                    # Provide specific error message based on whether user_id was provided
                    if not user_id:
                        error_message = 'User authentication required. Please sign in to start an interview.'
                    else:
                        error_message = 'User not found in database. Please contact support or try signing in again.'
                    
                    await send_if_open({
                        'type': 'error',
                        'data': {'message': error_message}
                    })
                    return
                
                print(f"✅ Conversation created successfully: {conversation['id']}")
                
                # Initialize session state
                self.active_sessions[session_id] = {
                    'created_at': datetime.now(),
                    'mode': mode,
                    'user_id': user_id,  # Store user_id in session
                    'conversation_id': conversation['id']  # Store for reference
                }
                
                # Initialize conversation flow management
                conversation_session = await conversation_integrator.handle_session_start(session_id, mode, user_id)
                print(f"🎯 Conversation flow initialized: {conversation_session.get('session_initialized', False)}")
                
                # Create Gemini session with enhanced context
                prompt_config = self.prompts.get(mode, self.prompts.get('amazon_interviewer', {}))
                base_system_instruction = prompt_config.get('system_instruction', 'You are a helpful AI interviewer.')
                
                # Add conversation flow context to system instruction
                initial_context = conversation_session.get('initial_context', '')
                enhanced_system_instruction = f"{base_system_instruction}\n\n{initial_context}"
                
                gemini_session = await self.create_gemini_session(session_id, enhanced_system_instruction)
                
                if not gemini_session:
                    print(f"❌ Failed to create AI session for {session_id}")
                    await send_if_open({
                        'type': 'error',
                        'data': {'message': 'Failed to create AI session'}
                    })
                    return
                
                # Start audio streaming for this session
                await self.start_audio_streaming(session_id, websocket)
                
                # Don't send initial message automatically - wait for user to start
                # User should click "Start Interview" button to begin the conversation
                
                await send_if_open({
                    'type': 'session_created',
                    'data': {
                        'session_id': session_id,
                        'mode': mode,
                        'conversation_id': conversation['id']
                    }
                })
            
            elif message_type == 'audio_data':
                audio_base64 = data.get('audio')
                if audio_base64 and session_id in self.gemini_sessions:
                    try:
                        audio_data = base64.b64decode(audio_base64)
                        
                        # Send audio directly to Gemini session (continuous streaming)
                        session_info = self.gemini_sessions[session_id]
                        session = session_info['session']
                        
                        await session.send_realtime_input(
                            audio=Blob(data=audio_data, mime_type="audio/pcm;rate=16000")
                        )
                        
                    except Exception as e:
                        print(f"❌ Error processing audio: {e}")
                        await send_if_open({
                            'type': 'error',
                            'data': {'message': 'Failed to process audio'}
                        })
            
            elif message_type == 'start_interview':
                # User clicked "Start Interview" - now send the initial message to Gemini
                if session_id in self.gemini_sessions:
                    try:
                        session_info = self.gemini_sessions[session_id]
                        session = session_info['session']
                        
                        # Get the interview mode to customize the initial message
                        session_state = self.active_sessions.get(session_id, {})
                        mode = session_state.get('mode', 'amazon_interviewer')
                        
                        # Send initial message to start the conversation
                        initial_message = "Hello! I'm ready to start the interview. Please introduce yourself briefly, and then I'll ask you some questions. What's your name and background?"
                        await session.send_realtime_input(text=initial_message)
                        
                        print(f"🎙️ Interview started for session {session_id} with mode {mode}")
                        
                        await send_if_open({
                            'type': 'interview_started',
                            'data': {'message': 'Interview has begun'}
                        })
                        
                    except Exception as e:
                        print(f"❌ Error starting interview: {e}")
                        await send_if_open({
                            'type': 'error',
                            'data': {'message': 'Failed to start interview'}
                        })
                else:
                    await send_if_open({
                        'type': 'error',
                        'data': {'message': 'No active session found'}
                    })
            
            elif message_type == 'text_input':
                text = data.get('text')
                if text:
                    # Get user_id from session
                    session_info = self.active_sessions.get(session_id, {})
                    user_id = session_info.get('user_id')
                    
                    # Add user message to transcript
                    await self.add_transcript(session_id, "user", text, "text", user_id=user_id)
                    
                    # Send to Gemini (convert text to simple prompt)
                    # For now, just echo back - you can enhance this to actually process with Gemini
                    response = f"I received your message: {text}"
                    await self.add_transcript(session_id, "assistant", response, "gemini", user_id=user_id)
                    
                    await send_if_open({
                        'type': 'text_response',
                        'data': {'text': response}
                    })
            
            elif message_type == 'end_session':
                print(f"🔚 Ending session {session_id} as requested by user")
                await self.close_session(session_id)
                
                # Don't send response - frontend already knows session is ending
                # and often closes WebSocket connection immediately
                print(f"✅ Session {session_id} ended successfully")
            
        except Exception as e:
            print(f"❌ Error handling message: {e}")
            traceback.print_exc()
            
            # Don't try to send error messages if this is a WebSocket connection error
            error_str = str(e).lower()
            error_type = str(type(e)).lower()
            
            # Check for various WebSocket connection closed indicators
            is_websocket_closed = (
                "connectionclosed" in error_type or
                "1005" in error_str or
                "no status received" in error_str or
                "connection closed" in error_str or
                "websocket" in error_type
            )
            
            if is_websocket_closed:
                print("🔌 WebSocket connection closed during message handling - skipping error response")
            else:
                print("🚨 Non-WebSocket error occurred, attempting to send error response")
                await send_if_open({
                    'type': 'error',
                    'data': {'message': str(e)}
                })

    async def add_buffered_transcript(self, session_id: str, speaker: str, text: str, provider: str = None, user_id: str = None):
        """Add transcript with buffering to accumulate partial responses into complete sentences"""
        if not text or not text.strip():
            return
            
        # Clean the text
        new_text = text.strip()
        
        # Ignore very short fragments (likely incomplete) unless they contain sentence endings
        if len(new_text) <= 2 and not any(end in new_text for end in ['.', '!', '?']):
            return
            
        # Initialize buffers if needed
        if session_id not in self.transcript_buffers:
            self.transcript_buffers[session_id] = {}
            self.transcript_timers[session_id] = {}
        
        if speaker not in self.transcript_buffers[session_id]:
            self.transcript_buffers[session_id][speaker] = ""
            self.transcript_timers[session_id][speaker] = {'last_update': datetime.now(), 'timer': None}
        
        # APPEND to buffer instead of replacing (Gemini sends incremental 3-char chunks)
        current_buffer = self.transcript_buffers[session_id][speaker]
        
        # Smart concatenation - no space needed since Gemini includes them
        self.transcript_buffers[session_id][speaker] = current_buffer + new_text
        
        # Update timing
        self.transcript_timers[session_id][speaker]['last_update'] = datetime.now()
        
        # Cancel existing timer
        if self.transcript_timers[session_id][speaker]['timer']:
            self.transcript_timers[session_id][speaker]['timer'].cancel()
        
        # Get the accumulated text
        accumulated_text = self.transcript_buffers[session_id][speaker].strip()
        
        # Check if we should save immediately (complete sentence indicators)
        should_save_now = (
            accumulated_text.endswith('.') or 
            accumulated_text.endswith('!') or 
            accumulated_text.endswith('?') or
            len(accumulated_text) > 300 or  # Save very long responses
            # Look for complete sentence patterns (sentence + space)
            '. ' in accumulated_text or '! ' in accumulated_text or '? ' in accumulated_text
        )
        
        if should_save_now:
            # Save immediately if we have a complete sentence
            if accumulated_text and len(accumulated_text) > 8:  # Require meaningful length
                await self.add_transcript(session_id, speaker, accumulated_text, provider, user_id=user_id)
                print(f"📝 {speaker.title()}: {accumulated_text}")
            # Clear the buffer
            self.transcript_buffers[session_id][speaker] = ""
            self.transcript_timers[session_id][speaker]['timer'] = None
        else:
            # Set a timer to save after 6 seconds of no updates (longer for complete sentences)
            async def save_buffered():
                await asyncio.sleep(6)
                if session_id in self.transcript_buffers and speaker in self.transcript_buffers[session_id]:
                    buffered_text = self.transcript_buffers[session_id][speaker].strip()
                    if buffered_text and len(buffered_text) > 8:  # Require meaningful length
                        await self.add_transcript(session_id, speaker, buffered_text, provider, user_id=user_id)
                        print(f"📝 {speaker.title()}: {buffered_text}")
                    self.transcript_buffers[session_id][speaker] = ""
                    if session_id in self.transcript_timers and speaker in self.transcript_timers[session_id]:
                        self.transcript_timers[session_id][speaker]['timer'] = None
            
            # Start the timer task
            timer_task = asyncio.create_task(save_buffered())
            self.transcript_timers[session_id][speaker]['timer'] = timer_task

# Global backend instance (will be initialized in lifespan)
backend = None

# FastAPI app with lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    global backend
    print("🚀 Starting Simple Supabase Backend...")
    
    # Initialize backend instance after FastAPI starts
    backend = SimpleSupabaseBackend()
    
    yield
    
    print("🛑 Shutting down Simple Supabase Backend...")
    # Cleanup any active sessions
    if backend and backend.active_sessions:
        for session_id in list(backend.active_sessions.keys()):
            await backend.close_session(session_id)

app = FastAPI(
    title="Coimbatore - Simple Supabase Backend",
    description="FastAPI backend with Supabase (conversations + transcripts only)",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Coimbatore - Simple Supabase Backend",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/api/health")
async def health_check():
    if not backend:
        return {"status": "initializing", "message": "Backend is still starting up"}
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "supabase": "connected" if backend.supabase else "not configured"
        },
        "active_sessions": len(backend.active_sessions)
    }

@app.get("/api/prompts")
async def get_prompts():
    if not backend:
        raise HTTPException(status_code=503, detail="Backend is still initializing")
    return backend.prompts

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    if not backend:
        await websocket.send_json({
            'type': 'error',
            'data': {'message': 'Backend is still initializing, please try again'}
        })
        await websocket.close()
        return
    
    backend.websocket_connections[session_id] = websocket
    
    try:
        while True:
            data = await websocket.receive_json()
            await backend.handle_websocket_message(websocket, session_id, data)
    except WebSocketDisconnect:
        print(f"🔌 WebSocket disconnected for session {session_id}")
    except Exception as e:
        print(f"❌ WebSocket error for session {session_id}: {e}")
    finally:
        if backend:
            await backend.close_session(session_id)

@app.get("/api/conversations/{session_id}")
async def get_conversation(session_id: str):
    """Get conversation details and transcripts"""
    if not backend:
        raise HTTPException(status_code=503, detail="Backend is still initializing")
    if not backend.supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        # Get conversation
        conversation = backend.supabase.table('conversations').select('*').eq('session_id', session_id).execute()
        if not conversation.data:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get transcripts
        transcripts = await backend.get_conversation_transcripts(session_id)
        
        return {
            'conversation': conversation.data[0],
            'transcripts': transcripts
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/transcripts/{session_id}")
async def get_transcripts(session_id: str, format: str = "json", speaker: str = None):
    """Get transcripts for a session with optional formatting and filtering"""
    if not backend:
        raise HTTPException(status_code=503, detail="Backend is still initializing")
    if not backend.supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        # Get transcripts
        transcripts = await backend.get_conversation_transcripts(session_id)
        
        if not transcripts:
            # Return empty array instead of 404 for sessions with no transcripts
            return {"format": format, "content": []}
        
        # Filter by speaker if specified
        if speaker:
            transcripts = [t for t in transcripts if t.get('speaker', '').lower() == speaker.lower()]
        
        # Format response based on requested format
        if format == "text":
            # Return as readable text format
            formatted_text = ""
            for transcript in transcripts:
                speaker_name = transcript.get('speaker', 'Unknown')
                text = transcript.get('text', '')
                timestamp = transcript.get('created_at', '')
                formatted_text += f"[{timestamp}] {speaker_name}: {text}\n\n"
            
            return {"format": "text", "content": formatted_text.strip()}
        
        elif format == "conversation":
            # Return as conversation format (alternating speakers)
            conversation = []
            for transcript in transcripts:
                conversation.append({
                    "speaker": transcript.get('speaker', 'Unknown'),
                    "text": transcript.get('text', ''),
                    "timestamp": transcript.get('created_at', ''),
                    "provider": transcript.get('provider', 'unknown')
                })
            
            return {"format": "conversation", "content": conversation}
        
        else:
            # Return raw JSON format
            return {"format": "json", "content": transcripts}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/conversations")
async def list_conversations():
    """List all conversations"""
    if not backend:
        raise HTTPException(status_code=503, detail="Backend is still initializing")
    if not backend.supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        result = backend.supabase.table('conversations').select('*').order('created_at', desc=True).execute()
        return result.data if result.data else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/conversations/{session_id}")
async def delete_conversation(session_id: str):
    """Delete a conversation and all its transcripts"""
    if not backend:
        raise HTTPException(status_code=503, detail="Backend is still initializing")
    if not backend.supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        # Close active session if running
        if session_id in backend.active_sessions:
            await backend.close_session(session_id)
        
        # Delete from database (transcripts will be deleted automatically due to CASCADE)
        result = backend.supabase.table('conversations').delete().eq('session_id', session_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {"message": "Conversation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test/create-sample-data")
async def create_sample_data():
    """Create sample conversation and transcript data for testing"""
    if not backend:
        raise HTTPException(status_code=503, detail="Backend is still initializing")
    if not backend.supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        import uuid
        
        # Create test session ID
        test_session_id = f"session_demo_{uuid.uuid4().hex[:6]}"
        
        # Create test conversation
        conversation_data = {
            "session_id": test_session_id,
            "mode": "technical_screening",
            "status": "completed", 
            "title": "Demo Technical Interview",
            "duration": 420,
            "performance_score": 8.5,
            "difficulty_level": "medium"
        }
        
        # Insert conversation
        conv_result = backend.supabase.table("conversations").insert(conversation_data).execute()
        
        if conv_result.data:
            # Create test transcripts
            test_transcripts = [
                {
                    "session_id": test_session_id,
                    "speaker": "assistant",
                    "text": "Hello! Welcome to your technical interview. I'm excited to work with you today. Let's start with some basics - can you tell me about your experience with Python?",
                    "provider": "gemini_text",
                    "confidence_score": 0.95
                },
                {
                    "session_id": test_session_id,
                    "speaker": "user", 
                    "text": "I have about 3 years of experience with Python. I've worked on web development using Django and Flask, data analysis with pandas, and some machine learning projects with scikit-learn.",
                    "provider": "user_input",
                    "confidence_score": 1.0
                },
                {
                    "session_id": test_session_id,
                    "speaker": "assistant",
                    "text": "That's great! Python is such a versatile language. Now, let's dive into a coding question. Can you write a function that finds the two numbers in an array that add up to a target sum?",
                    "provider": "gemini_text",
                    "confidence_score": 0.98
                },
                {
                    "session_id": test_session_id,
                    "speaker": "user",
                    "text": "Sure! I'll use a hash map approach for O(n) time complexity. Let me walk through the solution step by step.",
                    "provider": "user_input",
                    "confidence_score": 1.0
                },
                {
                    "session_id": test_session_id,
                    "speaker": "assistant", 
                    "text": "Perfect approach! The hash map solution is indeed optimal. Can you also explain the space complexity and any edge cases we should consider?",
                    "provider": "gemini_text",
                    "confidence_score": 0.96
                },
                {
                    "session_id": test_session_id,
                    "speaker": "user",
                    "text": "The space complexity is O(n) for the hash map. Edge cases include: empty array, array with less than 2 elements, no valid pair exists, and duplicate numbers.",
                    "provider": "user_input", 
                    "confidence_score": 1.0
                }
            ]
            
            # Insert transcripts
            for transcript in test_transcripts:
                backend.supabase.table("transcripts").insert(transcript).execute()
            
            return {
                "message": "Sample data created successfully",
                "session_id": test_session_id,
                "conversation_count": 1,
                "transcript_count": len(test_transcripts),
                "test_url": f"http://localhost:3001/dashboard"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create conversation")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating sample data: {str(e)}")

@app.get("/api/test/list-sessions")
async def list_sessions():
    """List all available session IDs for testing"""
    if not backend:
        raise HTTPException(status_code=503, detail="Backend is still initializing")
    if not backend.supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        # Get active sessions
        active_sessions = list(backend.active_sessions.keys()) if hasattr(backend, 'active_sessions') else []
        
        # Get sessions from database
        db_sessions = []
        try:
            result = backend.supabase.table("conversations").select("session_id, mode, status, created_at").limit(20).execute()
            if result.data:
                db_sessions = [
                    {
                        "session_id": row["session_id"],
                        "mode": row["mode"],
                        "status": row["status"],
                        "created_at": row["created_at"]
                    }
                    for row in result.data
                ]
        except Exception as db_error:
            print(f"Database query error: {db_error}")
        
        # Get sessions that have transcripts
        transcript_sessions = []
        try:
            transcript_result = backend.supabase.table("transcripts").select("session_id").limit(50).execute()
            if transcript_result.data:
                # Get unique session IDs
                unique_sessions = list(set([row["session_id"] for row in transcript_result.data if row["session_id"]]))
                transcript_sessions = unique_sessions
        except Exception as transcript_error:
            print(f"Transcript query error: {transcript_error}")
        
        return {
            "active_sessions": active_sessions,
            "database_sessions": db_sessions,
            "sessions_with_transcripts": transcript_sessions,
            "total_active": len(active_sessions),
            "total_database": len(db_sessions),
            "total_with_transcripts": len(transcript_sessions),
            "sample_test_ids": [
                "session_demo_001",
                "session_test_123", 
                "session_sample_456"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing sessions: {str(e)}")

# Include Clerk authentication routers if available
if CLERK_INTEGRATION_AVAILABLE:
    app.include_router(webhook_router)
    app.include_router(user_router)
    print("✅ Clerk authentication routers added")
else:
    print("⚠️ Clerk integration not available - user authentication disabled")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000) 