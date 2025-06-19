#!/usr/bin/env python3
"""
Debug script to understand exactly what transcript data Gemini Live API sends
"""

import os
import asyncio
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from google import genai
    from google.genai.types import LiveConnectConfig, Blob
    GEMINI_AVAILABLE = True
except ImportError:
    print("❌ Google Gemini SDK not installed. Install with: pip install google-genai")
    GEMINI_AVAILABLE = False

async def debug_gemini_transcripts():
    if not GEMINI_AVAILABLE:
        print("❌ Gemini SDK not available")
        return
    
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("❌ GOOGLE_API_KEY not found in environment")
        return
    
    print("🚀 Testing Gemini Live API transcript reception...")
    
    try:
        # Initialize Gemini client
        client = genai.Client(api_key=api_key)
        
        # Create enhanced configuration
        config = LiveConnectConfig(
            response_modalities=["AUDIO"],
            input_audio_transcription={},    # Enable user speech transcription
            output_audio_transcription={},   # Enable AI speech transcription
            system_instruction="You are a test assistant. Say a short greeting when the session starts."
        )
        
        print("🔗 Connecting to Gemini Live...")
        
        # Create session
        async with client.aio.live.connect(model="models/gemini-2.0-flash-live-001", config=config) as session:
            print("✅ Connected to Gemini Live!")
            
            # Send initial message to trigger a response
            await session.send_realtime_input(text="Say hello and introduce yourself briefly")
            print("📤 Sent initial message to Gemini")
            
            # Listen for responses
            response_count = 0
            max_responses = 20  # Limit to prevent infinite loop
            
            print("\n🎯 Listening for transcript responses...")
            print("=" * 60)
            
            turn = session.receive()
            async for response in turn:
                response_count += 1
                if response_count > max_responses:
                    print(f"\n⏹️ Reached maximum responses ({max_responses}), stopping...")
                    break
                
                print(f"\n📋 Response #{response_count}:")
                print(f"   Type: {type(response)}")
                
                # Check for audio data
                if hasattr(response, 'data') and response.data:
                    print(f"   🎵 Audio data: {len(response.data)} bytes")
                
                # Check for server_content
                if hasattr(response, 'server_content') and response.server_content:
                    server_content = response.server_content
                    print(f"   📝 Server content found")
                    
                    # Check output transcription (AI speech)
                    if hasattr(server_content, 'output_transcription') and server_content.output_transcription:
                        if hasattr(server_content.output_transcription, 'text'):
                            text = server_content.output_transcription.text
                            print(f"   🤖 AI Transcript: '{text}' (length: {len(text)})")
                    
                    # Check input transcription (user speech)
                    if hasattr(server_content, 'input_transcription') and server_content.input_transcription:
                        if hasattr(server_content.input_transcription, 'text'):
                            text = server_content.input_transcription.text
                            print(f"   👤 User Transcript: '{text}' (length: {len(text)})")
                    
                    # Check model turn
                    if hasattr(server_content, 'model_turn') and server_content.model_turn:
                        model_turn = server_content.model_turn
                        print(f"   📄 Model turn found")
                        
                        if hasattr(model_turn, 'parts') and model_turn.parts:
                            for i, part in enumerate(model_turn.parts):
                                if hasattr(part, 'text') and part.text:
                                    print(f"   📝 Model turn part {i}: '{part.text}' (length: {len(part.text)})")
                
                # Check direct response text
                if hasattr(response, 'text') and response.text:
                    print(f"   📄 Direct text: '{response.text}' (length: {len(response.text)})")
                
                # Print all attributes for debugging
                print(f"   🔍 Available attributes: {[attr for attr in dir(response) if not attr.startswith('_')]}")
                
                # Small delay to make output readable
                await asyncio.sleep(0.1)
            
            print("\n" + "=" * 60)
            print(f"✅ Completed! Processed {response_count} responses")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_gemini_transcripts()) 