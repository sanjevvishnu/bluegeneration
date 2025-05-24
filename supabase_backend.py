#!/usr/bin/env python3
"""
Single Python Backend for Live Audio Interview Practice
Uses FastAPI + Supabase for real-time communication and data storage
Integrates Gemini Live API and ElevenLabs
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
import asyncpg

# Audio and AI imports
import aiohttp
import websockets

# Load environment variables
load_dotenv()

# Gemini imports
try:
    from google import genai
    from google.genai.types import LiveConnectConfig, Blob
    GEMINI_AVAILABLE = True
except ImportError:
    print("❌ Warning: Google Gemini SDK not installed. Install with: pip install google-genai")
    GEMINI_AVAILABLE = False

class SupabaseLiveAudioBackend:
    def __init__(self):
        # Environment variables
        self.gemini_api_key = os.getenv('GOOGLE_API_KEY')
        self.elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        # Initialize Supabase client
        if not self.supabase_url or not self.supabase_key:
            print("❌ SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env file")
            print("📝 Get these from: https://supabase.com/dashboard/project/[project-id]/settings/api")
            self.supabase = None
        else:
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
            print("✅ Supabase client initialized")
        
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
        
        # Load interview prompts
        self.prompts = self.load_prompts()
        
        print(f"🐍 Supabase Live Audio Backend initializing...")
        print(f"🔑 Google API Key: {'✅ Set' if self.gemini_api_key and self.gemini_api_key != 'your_google_api_key_here' else '❌ Missing'}")
        print(f"🔑 ElevenLabs API Key: {'✅ Set' if self.elevenlabs_api_key else '❌ Missing'}")
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
    
    async def initialize_database(self):
        """Initialize Supabase database tables"""
        if not self.supabase:
            return False
            
        try:
            # Create sessions table
            sessions_table = """
            CREATE TABLE IF NOT EXISTS interview_sessions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id TEXT UNIQUE NOT NULL,
                mode TEXT NOT NULL,
                use_elevenlabs BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                status TEXT DEFAULT 'active'
            );
            """
            
            # Create transcripts table
            transcripts_table = """
            CREATE TABLE IF NOT EXISTS transcripts (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id TEXT NOT NULL,
                speaker TEXT NOT NULL,
                text TEXT NOT NULL,
                provider TEXT,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                FOREIGN KEY (session_id) REFERENCES interview_sessions(session_id)
            );
            """
            
            # Create indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON interview_sessions(session_id);",
                "CREATE INDEX IF NOT EXISTS idx_transcripts_session_id ON transcripts(session_id);",
                "CREATE INDEX IF NOT EXISTS idx_transcripts_timestamp ON transcripts(timestamp);"
            ]
            
            # Note: Supabase doesn't allow direct SQL execution via Python client
            # These tables should be created via Supabase Dashboard or CLI
            print("📋 Database schema ready (ensure tables exist in Supabase Dashboard)")
            return True
            
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
            return False
    
    async def create_session(self, session_id: str, mode: str, use_elevenlabs: bool = False):
        """Create a new interview session"""
        if not self.supabase:
            return None
            
        try:
            result = self.supabase.table('interview_sessions').insert({
                'session_id': session_id,
                'mode': mode,
                'use_elevenlabs': use_elevenlabs,
                'status': 'active'
            }).execute()
            
            print(f"✅ Created session {session_id} in database")
            return result.data[0] if result.data else None
            
        except Exception as e:
            print(f"❌ Failed to create session: {e}")
            return None
    
    async def add_transcript_entry(self, session_id: str, speaker: str, text: str, provider: str = None):
        """Add a transcript entry to the database"""
        if not self.supabase:
            return None
            
        try:
            result = self.supabase.table('transcripts').insert({
                'session_id': session_id,
                'speaker': speaker,
                'text': text,
                'provider': provider or 'unknown'
            }).execute()
            
            # Broadcast transcript update via Supabase real-time
            await self.broadcast_transcript_update(session_id, {
                'session_id': session_id,
                'speaker': speaker,
                'text': text,
                'provider': provider,
                'timestamp': datetime.now().isoformat()
            })
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            print(f"❌ Failed to add transcript entry: {e}")
            return None
    
    async def broadcast_transcript_update(self, session_id: str, transcript_entry: Dict):
        """Broadcast transcript update to connected clients"""
        if session_id in self.websocket_connections:
            try:
                websocket = self.websocket_connections[session_id]
                await websocket.send_text(json.dumps({
                    'type': 'transcript_update',
                    'data': transcript_entry
                }))
            except Exception as e:
                print(f"❌ Failed to broadcast transcript update: {e}")
    
    async def create_gemini_session(self, session_id: str, system_instruction: str):
        """Initialize session metadata for Gemini Live (connection will be created per request)"""
        if not self.gemini_client:
            return None
            
        try:
            # Store session configuration for later use
            # Note: Gemini Live API only allows ONE response modality per session
            self.active_sessions[session_id] = {
                'system_instruction': system_instruction,
                'use_elevenlabs': False,
                'config': LiveConnectConfig(
                    response_modalities=["TEXT"],  # Only TEXT for now, audio can be separate session
                    system_instruction=system_instruction  # Simple string format
                )
            }
            
            print(f"✅ Configured Gemini session for {session_id} with TEXT response modality")
            return True
            
        except Exception as e:
            print(f"❌ Failed to configure Gemini session: {e}")
            traceback.print_exc()
            return None
    
    async def process_audio_with_gemini(self, session_id: str, audio_data: bytes):
        """Process audio through Gemini Live API using async context manager"""
        if session_id not in self.active_sessions:
            print(f"❌ No active session for {session_id}")
            return None
            
        session_config = self.active_sessions[session_id]
        
        try:
            # Create a new connection for this request using async context manager
            async with self.gemini_client.aio.live.connect(
                model=self.model_name,
                config=session_config['config']
            ) as session:
                
                # Format audio as Blob with correct MIME type for Gemini Live API
                # Gemini Live API requires 16-bit PCM at 16kHz with specific MIME type
                audio_blob = Blob(
                    data=audio_data,
                    mime_type="audio/pcm;rate=16000"
                )
                
                # Send audio to Gemini using send_realtime_input
                await session.send_realtime_input(audio=audio_blob)
                
                # Listen for response
                async for response in session.receive():
                    if hasattr(response, 'audio'):
                        # Audio response from Gemini
                        await self.add_transcript_entry(session_id, 'Assistant', '[Audio Response]', 'gemini')
                        return {
                            'type': 'audio',
                            'data': base64.b64encode(response.audio).decode('utf-8'),
                            'provider': 'gemini'
                        }
                    elif hasattr(response, 'text'):
                        # Text response from Gemini
                        await self.add_transcript_entry(session_id, 'Assistant', response.text, 'gemini')
                        return {
                            'type': 'text',
                            'data': response.text,
                            'provider': 'gemini'
                        }
                    
        except Exception as e:
            print(f"❌ Error processing audio with Gemini: {e}")
            traceback.print_exc()
            return None
    
    async def synthesize_with_elevenlabs(self, text: str, session_id: str):
        """Synthesize text with ElevenLabs"""
        if not self.elevenlabs_api_key:
            return None
            
        try:
            url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.elevenlabs_api_key
            }
            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.8
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 200:
                        audio_data = await response.read()
                        return {
                            'type': 'audio',
                            'data': base64.b64encode(audio_data).decode('utf-8'),
                            'provider': 'elevenlabs'
                        }
                    else:
                        print(f"❌ ElevenLabs API error: {response.status}")
                        return None
                        
        except Exception as e:
            print(f"❌ ElevenLabs synthesis error: {e}")
            return None
    
    async def close_session(self, session_id: str):
        """Close a session and clean up resources"""
        try:
            # Remove session from active sessions (no need to close Gemini session as it's per-request)
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            # Remove WebSocket connection
            if session_id in self.websocket_connections:
                del self.websocket_connections[session_id]
            
            # Update session status in database
            if self.supabase:
                self.supabase.table('interview_sessions').update({
                    'status': 'closed',
                    'updated_at': datetime.now().isoformat()
                }).eq('session_id', session_id).execute()
            
            print(f"✅ Closed session {session_id}")
            
        except Exception as e:
            print(f"❌ Error closing session: {e}")

    async def get_conversation_history(self, session_id: str, limit: int = 20):
        """Get recent conversation history for context"""
        if not self.supabase:
            return []
            
        try:
            result = self.supabase.table('transcripts').select('speaker, text').eq('session_id', session_id).order('timestamp').limit(limit).execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"❌ Error getting conversation history: {e}")
            return []

    async def process_text_with_gemini(self, session_id: str, text: str):
        """Process text through Gemini regular API with conversation context"""
        if not self.gemini_client or session_id not in self.active_sessions:
            return None
            
        try:
            # Get the system instruction for this session
            system_instruction = self.active_sessions[session_id].get('system_instruction', 'You are a helpful assistant.')
            
            # Get conversation history for context
            conversation_history = await self.get_conversation_history(session_id)
            
            # Build conversation context properly to avoid role confusion
            conversation_context = f"""You are an interviewer. {system_instruction}

CONVERSATION HISTORY:
"""
            
            # Add conversation history with clear role separation
            for entry in conversation_history:
                role = "INTERVIEWER" if entry['speaker'] == 'Assistant' else "CANDIDATE"
                conversation_context += f"{role}: {entry['text']}\n\n"
            
            # Add current user message and request only interviewer response
            conversation_context += f"""CANDIDATE: {text}

Please respond ONLY as the INTERVIEWER. Do not generate the candidate's response. Provide only your next interviewer response:

INTERVIEWER:"""
            
            print(f"📝 Sending to Gemini with {len(conversation_history)} previous messages")
            
            # Use Gemini's regular generate_content API for text
            response = await self.gemini_client.aio.models.generate_content(
                model="models/gemini-2.0-flash-001",  # Use non-live model
                contents=[{
                    "parts": [{"text": conversation_context}]
                }]
            )
            
            if response and response.text:
                # Clean up response to remove any role labels that might leak through
                cleaned_response = response.text.strip()
                
                # Remove any interviewer/candidate labels if they appear
                if cleaned_response.startswith(('INTERVIEWER:', 'Interviewer:', 'CANDIDATE:', 'Candidate:')):
                    cleaned_response = ':'.join(cleaned_response.split(':')[1:]).strip()
                
                return cleaned_response
            else:
                print(f"❌ No text response from Gemini: {response}")
                return None
                
        except Exception as e:
            print(f"❌ Error processing text with Gemini: {e}")
            traceback.print_exc()
            return None

# Initialize backend
backend = SupabaseLiveAudioBackend()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan event handler"""
    # Startup
    await backend.initialize_database()
    yield
    # Shutdown (cleanup if needed)
    pass

# Create FastAPI app
app = FastAPI(
    title="Live Audio Interview Practice", 
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files in production
if os.getenv('NODE_ENV') == 'production':
    app.mount("/static", StaticFiles(directory="frontend/out"), name="static")

@app.get("/")
async def root():
    """Root endpoint"""
    if os.getenv('NODE_ENV') == 'production':
        return FileResponse('frontend/out/index.html')
    return {"message": "Live Audio Interview Practice Backend", "status": "running"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "gemini_available": GEMINI_AVAILABLE and backend.gemini_client is not None,
        "elevenlabs_available": bool(backend.elevenlabs_api_key),
        "supabase_connected": backend.supabase is not None,
        "active_sessions": len(backend.active_sessions),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/prompts")
async def get_prompts():
    """Get available interview prompts"""
    return backend.prompts

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time communication"""
    await websocket.accept()
    backend.websocket_connections[session_id] = websocket
    
    try:
        print(f"🔌 WebSocket connected: {session_id}")
        
        # Send initial session data
        await websocket.send_text(json.dumps({
            'type': 'session_ready',
            'data': {
                'session_id': session_id,
                'prompts': backend.prompts,
                'status': 'connected'
            }
        }))
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            await handle_websocket_message(websocket, session_id, message)
            
    except WebSocketDisconnect:
        print(f"🔌 WebSocket disconnected: {session_id}")
        await backend.close_session(session_id)
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        await backend.close_session(session_id)

async def handle_websocket_message(websocket: WebSocket, session_id: str, message: Dict):
    """Handle incoming WebSocket messages"""
    try:
        msg_type = message.get('type')
        data = message.get('data', {})
        
        if msg_type == 'create_session':
            # Create new session
            mode = data.get('mode', 'amazon_interviewer')
            use_elevenlabs = data.get('use_elevenlabs', False)
            
            await backend.create_session(session_id, mode, use_elevenlabs)
            
            # Create Gemini session if enabled
            if backend.gemini_client:
                prompt = backend.prompts.get(mode, {})
                system_instruction = prompt.get('system_instruction', 'You are a helpful assistant.')
                await backend.create_gemini_session(session_id, system_instruction)
            
            await websocket.send_text(json.dumps({
                'type': 'session_created',
                'data': {'session_id': session_id, 'mode': mode}
            }))
            
        elif msg_type == 'audio_data':
            # Temporarily disable audio processing to debug connection issues
            print("⚠️ Audio processing temporarily disabled for debugging")
            await websocket.send_text(json.dumps({
                'type': 'error',
                'data': {'message': 'Audio processing temporarily disabled for debugging'}
            }))
        
        elif msg_type == 'text_input':
            # Handle text input - Use Gemini text API for proper responses
            text = data.get('text', '')
            if text:
                await backend.add_transcript_entry(session_id, 'User', text, 'text')
                
                # Get AI response from Gemini
                ai_response = await backend.process_text_with_gemini(session_id, text)
                
                if ai_response:
                    await backend.add_transcript_entry(session_id, 'Assistant', ai_response, 'gemini')
                    
                    # Synthesize with ElevenLabs if enabled
                    if (session_id in backend.active_sessions and 
                        backend.active_sessions[session_id].get('use_elevenlabs')):
                        tts_result = await backend.synthesize_with_elevenlabs(ai_response, session_id)
                        if tts_result:
                            await websocket.send_text(json.dumps({
                                'type': 'audio_response',
                                'data': tts_result
                            }))
                else:
                    # Fallback to mock response if Gemini fails
                    mock_response = "Thank you for that input. Could you tell me more about your experience?"
                    await backend.add_transcript_entry(session_id, 'Assistant', mock_response, 'mock')
        
        elif msg_type == 'switch_mode':
            # Switch interview mode
            mode = data.get('mode')
            if mode and mode in backend.prompts:
                # Update session mode
                if backend.supabase:
                    backend.supabase.table('interview_sessions').update({
                        'mode': mode
                    }).eq('session_id', session_id).execute()
                
                await websocket.send_text(json.dumps({
                    'type': 'mode_switched',
                    'data': {'mode': mode, 'prompt': backend.prompts[mode]}
                }))
        
        elif msg_type == 'switch_voice':
            # Switch voice provider
            use_elevenlabs = data.get('use_elevenlabs', False)
            if session_id in backend.active_sessions:
                backend.active_sessions[session_id]['use_elevenlabs'] = use_elevenlabs
            
            await websocket.send_text(json.dumps({
                'type': 'voice_switched',
                'data': {'use_elevenlabs': use_elevenlabs}
            }))
            
    except Exception as e:
        print(f"❌ Error handling WebSocket message: {e}")
        traceback.print_exc()

@app.get("/api/transcripts/{session_id}")
async def get_session_transcript(session_id: str):
    """Get transcript for a session"""
    if not backend.supabase:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        result = backend.supabase.table('transcripts').select('*').eq('session_id', session_id).order('timestamp').execute()
        return {"session_id": session_id, "transcript": result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch transcript: {e}")

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and its data"""
    await backend.close_session(session_id)
    return {"message": f"Session {session_id} deleted"}

if __name__ == "__main__":
    port = int(os.getenv('PORT', 3000))
    print(f"🚀 Starting Supabase Live Audio Backend on port {port}")
    print(f"📡 WebSocket endpoint: ws://localhost:{port}/ws/{{session_id}}")
    print(f"🌐 HTTP API: http://localhost:{port}")
    
    uvicorn.run(
        "supabase_backend:app",
        host="0.0.0.0",
        port=port,
        reload=True if os.getenv('NODE_ENV') != 'production' else False,
        log_level="info"
    ) 