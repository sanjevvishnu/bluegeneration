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
        """Get Gemini configuration for the selected prompt"""
        config = {"response_modalities": ["AUDIO"]}
        
        if self.prompts_data and prompt_key in self.prompts_data:
            prompt_data = self.prompts_data[prompt_key]
            config["system_instruction"] = prompt_data["system_instruction"]
            print(f"🎯 Configured for: {prompt_data['name']}")
        else:
            print(f"📝 Using default configuration (no specific prompt)")
            
        return config
        
    async def handle_websocket_messages(self, websocket):
        """Handle incoming messages from WebSocket client"""
        self.websocket = websocket
        
        async for message in websocket:
            try:
                # Handle text messages (prompt selection, etc.)
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
                
                # Handle binary audio data
                elif isinstance(message, bytes):
                    self.audio_chunks_sent += 1
                    print(f"📤 Received PCM audio chunk #{self.audio_chunks_sent}: {len(message)} bytes")
                    
                    # Create PCM audio blob for Gemini Live API
                    from google.genai import types
                    blob = types.Blob(data=message, mime_type="audio/pcm")
                    
                    if self.session:
                        await self.session.send_realtime_input(audio=blob)
                        print(f"✅ Successfully sent PCM audio to Gemini")
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
                        
                        # Send raw PCM audio data back to frontend
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
        """Receive audio from Gemini Live API"""
        while True:
            try:
                turn = self.session.receive()
                async for response in turn:
                    if data := response.data:
                        print(f"🎤 Received audio from Gemini: {len(data)} bytes")
                        
                        # Put raw PCM audio data in queue to send to WebSocket
                        if self.audio_out_queue:
                            await self.audio_out_queue.put(data)
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
            await asyncio.sleep(0.5)
            
            # Get configuration for the selected prompt
            config = self.get_config_for_prompt(self.current_prompt)
            
            # Initialize connection to Gemini Live API with prompt-specific config
            async with client.aio.live.connect(model=MODEL, config=config) as session:
                self.session = session
                self.audio_out_queue = asyncio.Queue()
                
                print("✅ Connected to Gemini Live API")
                if self.current_prompt and self.prompts_data:
                    prompt_info = self.prompts_data.get(self.current_prompt, {})
                    print(f"🎯 Interview mode: {prompt_info.get('name', 'Unknown')}")
                
                print("🎵 Will output PCM audio at 24kHz for playback")
                
                # Start background tasks
                async with asyncio.TaskGroup() as tg:
                    # Note: message_handler is already running
                    tg.create_task(self.receive_audio_from_gemini())
                    tg.create_task(self.send_audio_to_websocket())
                    
                    # Wait for the message handler to complete
                    await message_handler
                    
        except websockets.exceptions.ConnectionClosed:
            print(f"🔌 Client disconnected: {websocket.remote_address}")
            print(f"📊 Session stats: {self.audio_chunks_sent} chunks sent, {self.audio_responses_received} responses received")
        except Exception as e:
            print(f"❌ Error handling client: {e}")
            traceback.print_exc()

async def main():
    print("🚀 Starting WebSocket server on localhost:8765")
    
    # Start WebSocket server
    async def handle_connection(websocket, path=None):
        audio_loop = WebSocketAudioLoop()
        await audio_loop.handle_client(websocket, path)
    
    server = await websockets.serve(
        handle_connection,
        "localhost", 
        8765,
        ping_interval=20,
        ping_timeout=10
    )
    
    print("🌐 WebSocket server is running. Open index.html in your browser.")
    print("🔑 Make sure GOOGLE_API_KEY environment variable is set!")
    print("🎤 Server expects raw PCM audio: 16kHz, mono, 16-bit samples")
    print("🎵 Server outputs raw PCM audio: 24kHz, mono, 16-bit samples")
    print("🎭 Supports interview prompts from prompts.json")
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