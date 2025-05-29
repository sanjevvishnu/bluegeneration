#!/usr/bin/env python3
"""
Main FastAPI Application for Live Audio Interview Practice
Real-time bidirectional wrapper around Google's cookbook Live API
"""

import asyncio
import json
import traceback
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Dict, Any
import base64

# FastAPI imports
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

# Google Gemini Live API (directly from cookbook)
from google import genai
from google.genai import types

# Local imports
from config import config
from models import ResponseModality, MessageType, TranscriptEntry, AudioData
from audio_processor import AudioProcessor
from session_manager import SessionManager
from supabase_client import SupabaseClient

# Cookbook constants
MODEL = "models/gemini-2.0-flash-live-001"
FORMAT = "pcm"
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

class WebSocketAudioLoop:
    """
    Real-time bidirectional audio loop based on Google's cookbook
    Maintains persistent Live API session per WebSocket connection
    """
    
    def __init__(self, websocket: WebSocket, session_id: str, session_info, supabase_client):
        self.websocket = websocket
        self.session_id = session_id
        self.session_info = session_info
        self.supabase_client = supabase_client
        
        # Live API client
        self.client = genai.Client(api_key=config.GOOGLE_API_KEY, http_options={"api_version": "v1beta"})
        self.session = None
        
        # Queues for real-time communication
        self.audio_in_queue = None
        self.out_queue = None
        
        # Task management
        self.tasks = []
        self.running = False
        
        print(f"🎙️ Created WebSocketAudioLoop for session {session_id}")
    
    async def start(self):
        """Start the persistent Live API session and background tasks"""
        try:
            print(f"🎬 Starting WebSocketAudioLoop for {self.session_id}")
            
            config_live = {"response_modalities": ["AUDIO"]}  # Exact cookbook config
            print(f"🔧 Live API config: {config_live} for {self.session_id}")
            
            # Create persistent Live API session using proper context manager
            print(f"📞 Creating Live API connection for {self.session_id}")
            self.live_session_manager = self.client.aio.live.connect(model=MODEL, config=config_live)
            
            print(f"🔗 Entering Live API session for {self.session_id}")
            self.session = await self.live_session_manager.__aenter__()
            print(f"✅ Live API session connected for {self.session_id}")
            print(f"🔍 Session type: {type(self.session)} for {self.session_id}")
            
            # Setup queues
            print(f"📦 Setting up queues for {self.session_id}")
            self.audio_in_queue = asyncio.Queue()
            self.out_queue = asyncio.Queue(maxsize=10)
            print(f"✅ Queues created for {self.session_id}")
            
            # Send initial conversation starter (REQUIRED by Live API)
            print(f"💬 Sending initial conversation starter for {self.session_id}")
            mode = self.session_info.mode
            
            if mode == 'amazon_interviewer':
                initial_message = "You are an Amazon technical interviewer. Start the interview with a brief greeting and ask your first technical question. Keep responses concise and conversational."
            elif mode == 'google_interviewer':
                initial_message = "You are a Google technical interviewer. Start the interview with a brief greeting and ask your first technical question. Keep responses concise and conversational."
            elif mode == 'general_interviewer':
                initial_message = "You are a technical interviewer. Start the interview with a brief greeting and ask your first technical question. Keep responses concise and conversational."
            else:
                initial_message = "You are a technical interviewer. Start the interview with a brief greeting and ask your first technical question. Keep responses concise and conversational."
            
            await self.session.send_client_content(
                turns={"role": "user", "parts": [{"text": initial_message}]}, 
                turn_complete=True
            )
            print(f"✅ Initial conversation starter sent for {self.session_id}")
            
            # Start background tasks (NO initial trigger like cookbook)
            print(f"🚀 Starting background tasks for {self.session_id}")
            self.running = True
            
            print(f"🔧 Creating _send_realtime task for {self.session_id}")
            send_task = asyncio.create_task(self._send_realtime())
            print(f"✅ Created _send_realtime task for {self.session_id}")
            
            print(f"🔧 Creating _receive_audio task for {self.session_id}")
            receive_task = asyncio.create_task(self._receive_audio())
            print(f"✅ Created _receive_audio task for {self.session_id}")
            
            print(f"🔧 Creating _send_audio_to_frontend task for {self.session_id}")
            frontend_task = asyncio.create_task(self._send_audio_to_frontend())
            print(f"✅ Created _send_audio_to_frontend task for {self.session_id}")
            
            self.tasks = [send_task, receive_task, frontend_task]
            
            print(f"✅ Started {len(self.tasks)} background tasks for {self.session_id}")
            
            # Debug: Check task states immediately
            for i, task in enumerate(self.tasks):
                print(f"🔍 Task {i+1} state: {task.get_name()} - Done: {task.done()} for {self.session_id}")
            
            # Debug: Log what we're waiting for
            print(f"⏳ Now waiting for audio input or Live API responses for {self.session_id}")
            
        except Exception as e:
            print(f"❌ Failed to start WebSocketAudioLoop: {e}")
            print(f"🔍 Exception type: {type(e)}")
            import traceback
            print(f"🔍 Full traceback: {traceback.format_exc()}")
            raise
    
    async def stop(self):
        """Stop the Live API session and background tasks"""
        print(f"🛑 Stopping WebSocketAudioLoop for {self.session_id}")
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Close Live API session using proper context manager
        if hasattr(self, 'live_session_manager') and self.live_session_manager:
            try:
                await self.live_session_manager.__aexit__(None, None, None)
            except Exception as e:
                print(f"⚠️ Error closing Live API session: {e}")
        
        print(f"✅ WebSocketAudioLoop stopped for {self.session_id}")
    
    async def send_audio(self, audio_data: bytes):
        """Send audio data to the Live API (called from WebSocket)"""
        if not self.running:
            return  # Don't send audio while not running
        
        try:
            # Put audio in queue for real-time sending (pure cookbook pattern)
            await self.out_queue.put({
                "data": audio_data, 
                "mime_type": "audio/pcm"
            })
            print(f"🎤 Queued audio: {len(audio_data)} bytes for {self.session_id}")
        except Exception as e:
            print(f"❌ Error queueing audio: {e}")
    
    async def _send_realtime(self):
        """Background task: Send audio from queue to Live API (exact cookbook pattern)"""
        print(f"🚀 Starting _send_realtime task for {self.session_id}")
        audio_count = 0
        while self.running:
            try:
                # Get audio from queue
                msg = await asyncio.wait_for(self.out_queue.get(), timeout=1.0)
                
                if msg and "data" in msg and "mime_type" in msg:
                    audio_data = msg["data"]
                    
                    if len(audio_data) > 0:
                        audio_count += 1
                        print(f"🎵 Processing audio chunk #{audio_count} ({len(audio_data)} bytes) for {self.session_id}")
                        
                        # Send audio to Live API in chunks (exact cookbook pattern)
                        for i in range(0, len(audio_data), CHUNK_SIZE):
                            if not self.running:
                                break
                            chunk = audio_data[i:i + CHUNK_SIZE]
                            blob = types.Blob(data=chunk, mime_type="audio/pcm")
                            
                            try:
                                await self.session.send_realtime_input(audio=blob)
                                print(f"✅ Sent chunk {i//CHUNK_SIZE + 1} ({len(chunk)} bytes) to Live API for {self.session_id}")
                            except Exception as e:
                                print(f"❌ Failed to send chunk to Live API: {e}")
                                break
                        
                        print(f"📤 Completed sending audio chunk #{audio_count} to Live API for {self.session_id}")
                        
                        # Debug: Check if this is the first audio and potentially trigger response
                        if audio_count == 1:
                            print(f"🎯 First audio sent! Live API should start processing for {self.session_id}")
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                if self.running:
                    print(f"❌ Error in _send_realtime for {self.session_id}: {e}")
                break
        
        print(f"🏁 _send_realtime task ended for {self.session_id}")
    
    async def _receive_audio(self):
        """Background task: Receive audio from Live API (EXACT cookbook pattern)"""
        try:
            print(f"🚀 Starting _receive_audio task for {self.session_id}")
            
            while self.running:
                try:
                    print(f"🎧 Waiting for Live API response for {self.session_id}")
                    
                    turn = self.session.receive()
                    print(f"📥 Got turn object from Live API for {self.session_id}")
                    
                    async for response in turn:
                        if not self.running:
                            break
                        
                        if data := response.data:
                            # Put raw audio data directly into queue without processing (cookbook)
                            self.audio_in_queue.put_nowait(data)
                            print(f"🔊 Received {len(data)} bytes from Live API for {self.session_id}")
                            continue  # CRUCIAL: continue after audio data (cookbook pattern)
                        
                        if text := response.text:
                            # Store text transcript and print like cookbook
                            transcript = TranscriptEntry(
                                session_id=self.session_id,
                                speaker='Assistant',
                                text=text,
                                provider='live_api',
                                timestamp=datetime.now()
                            )
                            await self.supabase_client.add_transcript_entry(transcript)
                            print(f"📝 Text response: {text}")
                    
                    # If you interrupt the model, it sends a turn_complete.
                    # For interruptions to work, we need to stop playback.
                    # So empty out the audio queue because it may have loaded
                    # much more audio than has played yet. (EXACT cookbook comment)
                    while not self.audio_in_queue.empty():
                        self.audio_in_queue.get_nowait()
                    
                except Exception as e:
                    if self.running:
                        print(f"❌ Error in _receive_audio for {self.session_id}: {e}")
                        await asyncio.sleep(1)
                        continue
                    break
            
            print(f"🏁 _receive_audio task ended for {self.session_id}")
            
        except Exception as e:
            print(f"💥 FATAL ERROR in _receive_audio task for {self.session_id}: {e}")
            import traceback
            print(f"🔍 Fatal traceback: {traceback.format_exc()}")
            raise
    
    async def _send_audio_to_frontend(self):
        """Background task: Send received audio to frontend via WebSocket (cookbook pattern)"""
        audio_buffer = b""  # Buffer to accumulate chunks (like cookbook)
        
        while self.running:
            try:
                # Get audio chunk from Live API (like cookbook play_audio)
                chunk = await asyncio.wait_for(self.audio_in_queue.get(), timeout=1.0)
                
                # Add chunk to buffer (cookbook pattern)
                audio_buffer += chunk
                
                # Send larger chunks to frontend for better quality (like cookbook CHUNK_SIZE * 2)
                while len(audio_buffer) >= CHUNK_SIZE * 4:  # 4KB chunks
                    # Extract a playback chunk
                    playback_chunk = audio_buffer[:CHUNK_SIZE * 4]
                    audio_buffer = audio_buffer[CHUNK_SIZE * 4:]
                    
                    try:
                        # Send audio to frontend
                        response_message = {
                            "type": "audio_chunk",
                            "data": {
                                "session_id": self.session_id,
                                "audio": base64.b64encode(playback_chunk).decode(),
                                "timestamp": datetime.now().isoformat()
                            }
                        }
                        
                        await self.websocket.send_text(json.dumps(response_message))
                        print(f"🔊 Sent {len(playback_chunk)} bytes to frontend for {self.session_id}")
                        
                    except Exception as e:
                        if self.running:
                            print(f"❌ Error sending to frontend for {self.session_id}: {e}")
                        break
                
            except asyncio.TimeoutError:
                # Send any remaining buffer (like cookbook)
                if audio_buffer and self.running:
                    try:
                        response_message = {
                            "type": "audio_chunk", 
                            "data": {
                                "session_id": self.session_id,
                                "audio": base64.b64encode(audio_buffer).decode(),
                                "timestamp": datetime.now().isoformat()
                            }
                        }
                        await self.websocket.send_text(json.dumps(response_message))
                        print(f"🔊 Sent final {len(audio_buffer)} bytes to frontend for {self.session_id}")
                        audio_buffer = b""
                    except Exception:
                        break
                continue
            except Exception as e:
                if self.running:
                    print(f"❌ Error in _send_audio_to_frontend for {self.session_id}: {e}")
                break

class LiveAudioBackend:
    """
    Main backend coordinator - thin wrapper around cookbook Live API
    """
    
    def __init__(self):
        self.config = config
        self.supabase_client = SupabaseClient()
        self.session_manager = SessionManager()
        self.audio_processor = AudioProcessor()
        
        # Active audio loops per session
        self.audio_loops: Dict[str, WebSocketAudioLoop] = {}
        self.websocket_connections: Dict[str, WebSocket] = {}
        
        print("🚀 Live Audio Backend initialized (Cookbook Wrapper)")
        self.print_status()
    
    def print_status(self):
        """Print system status"""
        print(f"🔑 Gemini API: {'✅ Connected' if config.GOOGLE_API_KEY else '❌ Not configured'}")
        print(f"🗄️ Supabase: {'✅ Connected' if self.supabase_client.is_available else '❌ Not available'}")
        print(f"🔊 Audio Processor: ✅ Ready")
        print(f"📋 Session Manager: ✅ Ready")
    
    async def startup(self):
        """Application startup tasks"""
        print("🔄 Starting up Live Audio Backend...")
        
        try:
            config.validate()
            print("✅ Configuration validated")
        except ValueError as e:
            print(f"❌ Configuration error: {e}")
            return False
        
        db_test = await self.supabase_client.test_connection()
        if db_test.get("connected"):
            print("✅ Database connection verified")
        else:
            print(f"❌ Database connection failed: {db_test.get('error')}")
        
        return True
    
    async def shutdown(self):
        """Application shutdown tasks"""
        print("🔄 Shutting down Live Audio Backend...")
        
        # Stop all audio loops
        for session_id, audio_loop in list(self.audio_loops.items()):
            await audio_loop.stop()
        
        # Close WebSocket connections
        for session_id in list(self.websocket_connections.keys()):
            try:
                websocket = self.websocket_connections[session_id]
                await websocket.close()
            except Exception:
                pass
        
        await self.session_manager.shutdown()
        print("✅ Live Audio Backend shutdown complete")
    
    async def handle_websocket_message(self, websocket: WebSocket, session_id: str, message: Dict):
        """Handle incoming WebSocket messages"""
        try:
            msg_type = MessageType(message.get('type'))
            data = message.get('data', {})
            
            if msg_type == MessageType.CREATE_SESSION:
                await self._handle_create_session(websocket, session_id, data)
                
            elif msg_type == MessageType.START_AUDIO:
                await self._handle_start_audio(websocket, session_id, data)
                
            elif msg_type == MessageType.AUDIO_DATA:
                await self._handle_audio_data(websocket, session_id, data)
                
            elif msg_type == MessageType.STOP_AUDIO:
                await self._handle_stop_audio(websocket, session_id, data)
                
            else:
                print(f"⚠️ Unknown message type: {msg_type}")
                
        except Exception as e:
            print(f"❌ Error handling WebSocket message: {e}")
            traceback.print_exc()
            await self._send_error(websocket, f"Error processing message: {str(e)}")
    
    async def _handle_create_session(self, websocket: WebSocket, session_id: str, data: Dict):
        """Create session but don't start audio loop yet"""
        mode = data.get('mode', 'amazon_interviewer')
        
        session_info = await self.session_manager.create_session(
            session_id, mode, ResponseModality.AUDIO, False
        )
        
        if not session_info:
            await self._send_error(websocket, "Failed to create session")
            return
        
        if self.supabase_client.is_available:
            await self.supabase_client.create_session_record(session_info)
        
        await websocket.send_text(json.dumps({
            'type': MessageType.SESSION_CREATED.value,
            'data': {
                'session_id': session_id, 
                'mode': mode,
                'status': 'ready_for_audio'
            }
        }))
        
        print(f"✅ Session {session_id} created and ready")
    
    async def _handle_start_audio(self, websocket: WebSocket, session_id: str, data: Dict):
        """Start the persistent Live API audio session"""
        if session_id in self.audio_loops:
            print(f"⚠️ Audio loop already running for {session_id}")
            return
        
        session_info = await self.session_manager.get_session(session_id)
        if not session_info:
            await self._send_error(websocket, "Session not found")
            return
        
        try:
            # Create and start audio loop
            audio_loop = WebSocketAudioLoop(websocket, session_id, session_info, self.supabase_client)
            await audio_loop.start()
            
            self.audio_loops[session_id] = audio_loop
            
            await websocket.send_text(json.dumps({
                'type': 'audio_started',
                'data': {
                    'session_id': session_id,
                    'status': 'live_api_connected'
                }
            }))
            
            print(f"🎙️ Audio session started for {session_id}")
            
        except Exception as e:
            print(f"❌ Failed to start audio session: {e}")
            await self._send_error(websocket, f"Failed to start audio: {str(e)}")
    
    async def _handle_audio_data(self, websocket: WebSocket, session_id: str, data: Dict):
        """Send audio data to the persistent Live API session"""
        if session_id not in self.audio_loops:
            await self._send_error(websocket, "Audio session not started")
            return
        
        audio_base64 = data.get('audio') or data.get('audio_data', '')
        if not audio_base64:
            return
        
        try:
            audio_bytes = base64.b64decode(audio_base64)
            
            # Process WebM to PCM if needed
            try:
                processed_audio = self.audio_processor.process_webm_to_pcm(
                    AudioData(data=audio_bytes, sample_rate=16000, channels=1, format="webm")
                )
                if processed_audio:
                    audio_bytes = processed_audio.data
            except Exception as e:
                print(f"⚠️ Using raw audio data: {e}")
            
            # Send to persistent Live API session
            audio_loop = self.audio_loops[session_id]
            await audio_loop.send_audio(audio_bytes)
            
        except Exception as e:
            print(f"❌ Error processing audio data: {e}")
    
    async def _handle_stop_audio(self, websocket: WebSocket, session_id: str, data: Dict):
        """Stop the persistent Live API audio session"""
        if session_id in self.audio_loops:
            audio_loop = self.audio_loops[session_id]
            await audio_loop.stop()
            del self.audio_loops[session_id]
            
            await websocket.send_text(json.dumps({
                'type': 'audio_stopped',
                'data': {'session_id': session_id}
            }))
            
            print(f"🛑 Audio session stopped for {session_id}")
    
    async def _send_error(self, websocket: WebSocket, message: str):
        """Send error message to client"""
        try:
            await websocket.send_text(json.dumps({
                'type': MessageType.ERROR.value,
                'data': {'message': message}
            }))
        except Exception as e:
            print(f"❌ Failed to send error message: {e}")

# Initialize backend
backend = LiveAudioBackend()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan event handler"""
    startup_success = await backend.startup()
    if not startup_success:
        print("❌ Failed to start backend")
    
    yield
    
    await backend.shutdown()

# Create FastAPI app
app = FastAPI(
    title="Live Audio Interview Practice",
    version="3.0.0",
    description="Real-time bidirectional wrapper around Google's cookbook Live API",
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

# Routes
@app.get("/")
async def root():
    return {
        "message": "Live Audio Interview Practice Backend v3.0 - Cookbook Wrapper",
        "status": "running",
        "active_sessions": len(backend.audio_loops),
        "components": {
            "gemini": bool(config.GOOGLE_API_KEY),
            "supabase": backend.supabase_client.is_available
        }
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_audio_sessions": len(backend.audio_loops),
        "components": {
            "gemini_available": bool(config.GOOGLE_API_KEY),
            "supabase_connected": backend.supabase_client.is_available
        }
    }

@app.get("/api/prompts")
async def get_prompts():
    return backend.session_manager.get_prompts()

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time bidirectional communication"""
    await websocket.accept()
    backend.websocket_connections[session_id] = websocket
    
    try:
        print(f"🔌 WebSocket connected: {session_id}")
        
        # Send initial session data
        await websocket.send_text(json.dumps({
            'type': MessageType.SESSION_READY.value,
            'data': {
                'session_id': session_id,
                'prompts': backend.session_manager.get_prompts(),
                'status': 'connected'
            }
        }))
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await backend.handle_websocket_message(websocket, session_id, message)
            
    except WebSocketDisconnect:
        print(f"🔌 WebSocket disconnected: {session_id}")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
    finally:
        # Cleanup
        if session_id in backend.websocket_connections:
            del backend.websocket_connections[session_id]
        
        # Stop audio loop if running
        if session_id in backend.audio_loops:
            await backend.audio_loops[session_id].stop()
            del backend.audio_loops[session_id]
        
        await backend.session_manager.close_session(session_id)

if __name__ == "__main__":
    print(f"🚀 Starting Live Audio Interview Practice Backend v3.0 (Cookbook Wrapper)")
    print(f"📡 WebSocket endpoint: ws://localhost:{config.PORT}/ws/{{session_id}}")
    print(f"🌐 HTTP API: http://localhost:{config.PORT}")
    
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.is_development(),
        log_level="info"
    ) 