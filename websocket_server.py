# -*- coding: utf-8 -*-
import asyncio
import base64
import io
import os
import sys
import traceback
import websockets
import json

from google import genai

if sys.version_info < (3, 11, 0):
    import taskgroup, exceptiongroup
    asyncio.TaskGroup = taskgroup.TaskGroup
    asyncio.ExceptionGroup = exceptiongroup.ExceptionGroup

MODEL = "models/gemini-2.0-flash-live-001"

client = genai.Client(http_options={"api_version": "v1beta"})

class WebSocketAudioLoop:
    def __init__(self):
        self.session = None
        self.websocket = None
        self.audio_out_queue = None
        self.audio_chunks_sent = 0
        self.audio_responses_received = 0
        self.current_prompt = None
        self.prompts_data = None
        
    def load_prompts(self):
        """Load prompts from prompts.json"""
        try:
            with open('prompts.json', 'r') as f:
                self.prompts_data = json.load(f)
                print(f"📝 Loaded {len(self.prompts_data)} interview prompts")
        except Exception as e:
            print(f"⚠️ Could not load prompts.json: {e}")
            self.prompts_data = {}
    
    def get_config_for_prompt(self, prompt_key):
        """Get Gemini configuration for the selected prompt with VAD settings"""
        # Enhanced configuration for real-time audio conversation with VAD
        config = {
            "response_modalities": ["AUDIO"],
            "realtime_input_config": {
                "automatic_activity_detection": {
                    "disabled": False,  # Enable automatic VAD
                    "start_of_speech_sensitivity": "START_SENSITIVITY_MEDIUM",  # More balanced detection  
                    "end_of_speech_sensitivity": "END_SENSITIVITY_MEDIUM",    # Balanced end detection
                    "prefix_padding_ms": 200,   # Shorter padding for faster response
                    "silence_duration_ms": 600, # Shorter silence for quicker turn-taking
                },
                "turn_detection": {
                    "create_new_turn_on_interruption": True,  # Create new turn when interrupted
                    "turn_timeout_ms": 5000  # 5 second turn timeout
                }
            }
        }
        
        if self.prompts_data and prompt_key in self.prompts_data:
            prompt_data = self.prompts_data[prompt_key]
            # Enhanced system instruction for audio conversation with interruption
            audio_instruction = """

IMPORTANT REAL-TIME CONVERSATION RULES:
1. You MUST respond with AUDIO speech, not text
2. Listen carefully to what the user says and respond directly to their input
3. Keep your responses conversational and natural (2-3 sentences max)
4. If you detect the user starting to speak while you're talking, STOP immediately
5. Be interactive and responsive - this is a real-time voice conversation
6. Acknowledge what the user said before asking new questions
7. Speak clearly and at a normal pace
8. When interrupted, gracefully yield the conversation turn
9. Keep responses concise to allow for natural turn-taking
10. Be prepared to be interrupted at any time - this is normal in conversation

Remember: This is a real-time voice conversation with natural interruptions."""
            
            config["system_instruction"] = prompt_data["system_instruction"] + audio_instruction
            print(f"🎯 Configured for: {prompt_data['name']} with enhanced VAD and interruption handling")
        else:
            config["system_instruction"] = """You are a helpful technical interviewer conducting a real-time voice conversation.

IMPORTANT REAL-TIME CONVERSATION RULES:
1. You MUST respond with AUDIO speech, not text
2. Listen carefully to what the user says and respond directly to their input
3. Keep your responses conversational and natural (2-3 sentences max)
4. If you detect the user starting to speak while you're talking, STOP immediately
5. Be interactive and responsive - this is a real-time voice conversation
6. Acknowledge what the user said before asking new questions
7. Speak clearly and at a normal pace
8. When interrupted, gracefully yield the conversation turn
9. Keep responses concise to allow for natural turn-taking
10. Be prepared to be interrupted at any time - this is normal in conversation

Remember: This is a real-time voice conversation with natural interruptions."""
            print(f"📝 Using enhanced default configuration with VAD for audio conversation")
            
        return config
        
    async def handle_websocket_messages(self, websocket):
        """Handle incoming messages from WebSocket client"""
        self.websocket = websocket
        
        async for message in websocket:
            try:
                # Handle text messages (prompt selection, audio data, etc.)
                if isinstance(message, str):
                    data = json.loads(message)
                    
                    if data.get('type') == 'prompt_selection':
                        prompt_key = data.get('prompt')
                        self.current_prompt = prompt_key
                        print(f"🎭 Prompt selected: {prompt_key}")
                        
                        # Send confirmation back to frontend
                        await websocket.send(json.dumps({
                            'type': 'prompt_configured',
                            'prompt': prompt_key
                        }))
                        
                        # Note: We'll configure Gemini when we start the session
                        continue
                    
                    elif data.get('type') == 'audio_data':
                        # Handle audio data from frontend
                        audio_data = data.get('data', {})
                        base64_audio = audio_data.get('audio')
                        audio_format = audio_data.get('format', 'webm')
                        
                        if base64_audio and self.session:
                            self.audio_chunks_sent += 1
                            print(f"📤 Received {audio_format} audio chunk #{self.audio_chunks_sent}")
                            
                            try:
                                # Decode base64 audio
                                audio_bytes = base64.b64decode(base64_audio)
                                print(f"📤 Decoded audio: {len(audio_bytes)} bytes")
                                
                                # Gemini Live API only supports specific formats
                                from google.genai import types
                                
                                # Handle different audio formats
                                if 'webm' in audio_format.lower() or audio_format.lower() == 'auto' or audio_format.lower() == 'browser-default':
                                    # Default to WebM for auto/browser-default since most browsers use WebM
                                    blob = types.Blob(data=audio_bytes, mime_type="audio/webm")
                                    await self.session.send_realtime_input(audio=blob)
                                    print(f"✅ Successfully sent WebM audio to Gemini (original format: {audio_format})")
                                elif 'wav' in audio_format.lower():
                                    # Try to send WAV
                                    blob = types.Blob(data=audio_bytes, mime_type="audio/wav")
                                    await self.session.send_realtime_input(audio=blob)
                                    print(f"✅ Successfully sent WAV audio to Gemini")
                                elif 'ogg' in audio_format.lower() or 'opus' in audio_format.lower():
                                    # Try OGG/Opus as WebM (they're similar)
                                    blob = types.Blob(data=audio_bytes, mime_type="audio/webm")
                                    await self.session.send_realtime_input(audio=blob)
                                    print(f"✅ Successfully sent OGG as WebM audio to Gemini")
                                else:
                                    # Unknown format, try as WebM anyway
                                    print(f"⚠️ Unknown audio format: {audio_format}, trying as WebM...")
                                    blob = types.Blob(data=audio_bytes, mime_type="audio/webm")
                                    await self.session.send_realtime_input(audio=blob)
                                    print(f"✅ Successfully sent unknown format as WebM audio to Gemini")
                                
                            except Exception as e:
                                print(f"❌ Error processing audio data: {e}")
                        else:
                            print("⚠️ No audio data or session available")
                        continue
                    
                    elif data.get('type') == 'user_interruption':
                        print("⚡ Received user interruption signal - clearing audio queue immediately!")
                        # Clear the audio queue to stop AI playback
                        if self.audio_out_queue:
                            while not self.audio_out_queue.empty():
                                try:
                                    self.audio_out_queue.get_nowait()
                                except:
                                    break
                            print("🛑 Audio queue cleared due to user interruption")
                        continue
                
                # Handle binary audio data (raw PCM from frontend)
                elif isinstance(message, bytes):
                    self.audio_chunks_sent += 1
                    print(f"📤 Received raw PCM audio chunk #{self.audio_chunks_sent}: {len(message)} bytes")
                    
                    # Create PCM audio blob for Gemini Live API with explicit rate
                    from google.genai import types
                    blob = types.Blob(data=message, mime_type="audio/pcm;rate=16000")
                    
                    if self.session:
                        await self.session.send_realtime_input(audio=blob)
                        print(f"✅ Successfully sent PCM audio to Gemini (16kHz, mono, 16-bit)")
                        print(f"🎧 Total audio chunks sent so far: {self.audio_chunks_sent}")
                    else:
                        print("⚠️ No active Gemini session")
                
            except json.JSONDecodeError:
                print(f"⚠️ Could not parse message as JSON")
            except Exception as e:
                print(f"❌ Error processing WebSocket message: {e}")
                traceback.print_exc()
                
    async def send_audio_to_websocket(self):
        """Send audio responses back to WebSocket client"""
        while True:
            try:
                if self.audio_out_queue and not self.audio_out_queue.empty():
                    audio_data = await self.audio_out_queue.get()
                    if self.websocket:
                        self.audio_responses_received += 1
                        print(f"🔊 Sending audio response #{self.audio_responses_received}: {len(audio_data)} bytes to frontend")
                        
                        # Send raw PCM audio data back to frontend as binary
                        await self.websocket.send(audio_data)
                        print(f"✅ Audio response sent successfully")
                    else:
                        print("⚠️ No WebSocket connection available")
                        break
            except websockets.exceptions.ConnectionClosed:
                print("🔌 WebSocket connection closed, stopping audio send")
                break
            except Exception as e:
                print(f"❌ Error sending audio to WebSocket: {e}")
                # Don't break here, just log and continue
                pass
            await asyncio.sleep(0.01)
                
    async def receive_audio_from_gemini(self):
        """Receive audio from Gemini Live API with interruption handling"""
        print("🎧 Starting to listen for audio responses from Gemini...")
        while True:
            try:
                turn = self.session.receive()
                async for response in turn:
                    # Enhanced interruption detection
                    if hasattr(response, 'server_content') and response.server_content:
                        # Check for interruption signals
                        if hasattr(response.server_content, 'interrupted') and response.server_content.interrupted:
                            print("⚡ User interrupted model - clearing audio queue")
                            # Clear the audio queue to stop playback immediately
                            while not self.audio_out_queue.empty():
                                try:
                                    self.audio_out_queue.get_nowait()
                                except:
                                    break
                            continue
                        
                        # Check for turn completion
                        if hasattr(response.server_content, 'turn_complete') and response.server_content.turn_complete:
                            print("🔄 Turn completed by Gemini")
                            continue
                    
                    # Handle turn detection
                    if hasattr(response, 'server_content') and response.server_content:
                        if hasattr(response.server_content, 'model_turn'):
                            model_turn = response.server_content.model_turn
                            if hasattr(model_turn, 'parts'):
                                for part in model_turn.parts:
                                    if hasattr(part, 'interruption_detected') and part.interruption_detected:
                                        print("⚡ Interruption detected - user is speaking!")
                                        # Clear audio queue immediately
                                        while not self.audio_out_queue.empty():
                                            try:
                                                self.audio_out_queue.get_nowait()
                                            except:
                                                break
                                        continue
                    
                    # Handle audio data
                    if data := response.data:
                        print(f"🎤 Received audio from Gemini: {len(data)} bytes")
                        
                        # Put raw PCM audio data in queue to send to WebSocket
                        if self.audio_out_queue:
                            await self.audio_out_queue.put(data)
                            print(f"📥 Audio queued for sending to frontend")
                        else:
                            print("⚠️ No audio output queue available")
                        continue
                    if text := response.text:
                        print(f"💬 Gemini text: {text}")
                        
            except Exception as e:
                print(f"❌ Error receiving from Gemini: {e}")
                traceback.print_exc()
                break

    async def handle_client(self, websocket, path=None):
        """Handle new WebSocket client connection"""
        print(f"🔗 New client connected: {websocket.remote_address}")
        
        try:
            # Load prompts data
            self.load_prompts()
            
            # Start handling WebSocket messages (including prompt selection)
            message_handler = asyncio.create_task(self.handle_websocket_messages(websocket))
            
            # Wait a bit for prompt selection
            print("⏳ Waiting for prompt selection...")
            await asyncio.sleep(0.5)
            
            # Get configuration for the selected prompt with VAD settings
            config = self.get_config_for_prompt(self.current_prompt)
            print(f"🔧 Gemini config with VAD: {config}")
            
            # Initialize connection to Gemini Live API with prompt-specific config
            print("🔄 Attempting to connect to Gemini Live API...")
            try:
                async with client.aio.live.connect(model=MODEL, config=config) as session:
                    self.session = session
                    self.audio_out_queue = asyncio.Queue()
                    
                    print("✅ Connected to Gemini Live API with VAD enabled")
                    if self.current_prompt and self.prompts_data:
                        prompt_info = self.prompts_data.get(self.current_prompt, {})
                        print(f"🎯 Interview mode: {prompt_info.get('name', 'Unknown')}")
                    
                    print("🎵 Will output PCM audio at 24kHz for playback")
                    print("⚡ VAD enabled: Automatic voice activity detection with interruption support")
                    
                    # Send initial message to start the conversation
                    print("💬 Sending initial message to Gemini...")
                    initial_message = "Hello! I'm ready to start the interview. Please introduce yourself briefly, and then I'll ask you some questions. What's your name and background?"
                    await session.send_realtime_input(text=initial_message)
                    print(f"💬 Sent initial message to Gemini: {initial_message}")
                    
                    # Start background tasks
                    print("🚀 Starting background tasks...")
                    async with asyncio.TaskGroup() as tg:
                        # Note: message_handler is already running
                        tg.create_task(self.receive_audio_from_gemini())
                        tg.create_task(self.send_audio_to_websocket())
                        
                        # Wait for the message handler to complete
                        await message_handler
                        
            except Exception as gemini_error:
                print(f"❌ Failed to connect to Gemini Live API: {gemini_error}")
                print(f"❌ Gemini error type: {type(gemini_error)}")
                traceback.print_exc()
                # Send error to client
                await websocket.send(json.dumps({
                    'type': 'error',
                    'data': {'message': f'Failed to connect to Gemini: {str(gemini_error)}'}
                }))
                    
        except websockets.exceptions.ConnectionClosed:
            print(f"🔌 Client disconnected: {websocket.remote_address}")
            print(f"📊 Session stats: {self.audio_chunks_sent} chunks sent, {self.audio_responses_received} responses received")
        except Exception as e:
            print(f"❌ Error handling client: {e}")
            print(f"❌ Error type: {type(e)}")
            traceback.print_exc()

async def main():
    # Get configuration from environment variables
    HOST = os.getenv('HOST', '0.0.0.0')  # Allow external connections in production
    PORT = int(os.getenv('PORT', 8765))
    
    print(f"🚀 Starting WebSocket server on {HOST}:{PORT}")
    
    # Start WebSocket server
    async def handle_connection(websocket, path=None):
        audio_loop = WebSocketAudioLoop()
        await audio_loop.handle_client(websocket, path)
    
    server = await websockets.serve(
        handle_connection,
        HOST, 
        PORT,
        ping_interval=20,
        ping_timeout=10,
        close_timeout=10
    )
    
    print(f"🌐 WebSocket server is running on ws://{HOST}:{PORT}")
    print("🔑 Make sure GOOGLE_API_KEY environment variable is set!")
    print("🎤 Server expects raw PCM audio: 16kHz, mono, 16-bit samples")
    print("🎵 Server outputs raw PCM audio: 24kHz, mono, 16-bit samples")
    print("🎭 Supports interview prompts from prompts.json")
    print("⚡ VAD enabled: Automatic voice activity detection with interruption support")
    await server.wait_closed()

if __name__ == "__main__":
    # Check if API key is set
    if not os.getenv('GOOGLE_API_KEY'):
        print("❌ ERROR: GOOGLE_API_KEY environment variable not set!")
        print("Please set it with: export GOOGLE_API_KEY='your_api_key_here'")
        sys.exit(1)
        
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        traceback.print_exc() 