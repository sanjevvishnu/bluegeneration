#!/usr/bin/env python3
"""
Quick targeted test for Gemini Live voice issue
"""

import asyncio
import numpy as np
from config import config
from models import SessionInfo, ResponseModality, AudioData
from gemini_live_client import GeminiLiveClient
from google.genai.types import LiveConnectConfig

async def test_gemini_live_audio():
    """Test Gemini Live API with audio input"""
    print("🎤 Testing Gemini Live Audio...")
    
    # Initialize client
    client = GeminiLiveClient()
    if not client.is_available:
        print("❌ Gemini client not available")
        return
    
    # Create simple test audio (1 second, 440Hz sine wave)
    sample_rate = 16000
    duration = 1.0  # 1 second
    samples = int(sample_rate * duration)
    
    t = np.linspace(0, duration, samples, False)
    wave = np.sin(2 * np.pi * 440 * t)  # 440Hz tone
    audio_16bit = (wave * 32767).astype(np.int16)
    
    audio_data = AudioData(
        data=audio_16bit.tobytes(),
        sample_rate=sample_rate,
        channels=1,
        format="pcm"
    )
    
    print(f"🔊 Created test audio: {len(audio_data.data)} bytes, {audio_data.mime_type}")
    
    # Create session info
    session_info = SessionInfo(
        session_id="quick-test",
        mode="amazon_interviewer",
        response_modality=ResponseModality.AUDIO,
        system_instruction="You are a helpful interviewer. Say 'I can hear you' when you receive audio."
    )
    
    try:
        # Test with timeout
        print("🔄 Starting Live API session with timeout...")
        
        async with asyncio.timeout(10):  # 10 second timeout
            live_config = client.create_session_config(session_info)
            
            async with client.client.aio.live.connect(
                model=config.GEMINI_MODEL,
                config=live_config
            ) as session:
                print("✅ Connected to Live API")
                
                # Send audio with Blob
                from google.genai.types import Blob
                audio_blob = Blob(
                    data=audio_data.data,
                    mime_type=audio_data.mime_type
                )
                
                print("📤 Sending audio data...")
                await session.send_realtime_input(audio=audio_blob)
                print("✅ Audio sent successfully")
                
                # Listen for responses with timeout
                response_count = 0
                async for response in session.receive():
                    response_count += 1
                    print(f"📨 Response {response_count}: {type(response)}")
                    
                    if hasattr(response, 'text') and response.text:
                        print(f"📝 Text: {response.text}")
                    
                    if hasattr(response, 'audio') and response.audio:
                        print(f"🔊 Audio: {len(response.audio)} bytes")
                    
                    if hasattr(response, 'server_content') and response.server_content:
                        if hasattr(response.server_content, 'turn_complete') and response.server_content.turn_complete:
                            print("✅ Turn complete signal received")
                            break
                    
                    # Prevent infinite loop
                    if response_count >= 5:
                        print("⏹️ Stopping after 5 responses")
                        break
                
                print(f"🎯 Received {response_count} responses total")
                
    except asyncio.TimeoutError:
        print("⏰ Test timed out - this indicates the Live API is hanging")
        print("💡 This suggests the audio format or API usage needs adjustment")
        return False
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("✅ Audio test completed successfully")
    return True

async def test_gemini_live_text_only():
    """Test Gemini Live API with TEXT modality"""
    print("📝 Testing Gemini Live TEXT mode...")
    
    client = GeminiLiveClient()
    if not client.is_available:
        print("❌ Gemini client not available")
        return False
    
    session_info = SessionInfo(
        session_id="text-test",
        mode="amazon_interviewer",
        response_modality=ResponseModality.TEXT,
        system_instruction="You are a helpful interviewer. Respond briefly."
    )
    
    try:
        # Use text processing method
        response = await client.process_text_message(
            session_info, 
            "Hello, can you hear me?",
            []
        )
        
        if response:
            print(f"✅ Text response: {response.data[:100]}...")
            return True
        else:
            print("❌ No text response received")
            return False
            
    except Exception as e:
        print(f"❌ Text test failed: {e}")
        return False

async def main():
    """Run quick tests"""
    print("🔍 Quick Gemini Live Voice Debug")
    print("=" * 40)
    
    # Test 1: Text mode (should work)
    text_result = await test_gemini_live_text_only()
    print(f"📊 Text mode: {'✅ PASS' if text_result else '❌ FAIL'}")
    
    print("\n" + "-" * 40)
    
    # Test 2: Audio mode (may hang)
    audio_result = await test_gemini_live_audio()
    print(f"📊 Audio mode: {'✅ PASS' if audio_result else '❌ FAIL'}")
    
    print("\n" + "=" * 40)
    if text_result and audio_result:
        print("🎉 Both modes working!")
    elif text_result and not audio_result:
        print("⚠️ Text works, Audio has issues")
    else:
        print("❌ Both modes have issues")

if __name__ == "__main__":
    asyncio.run(main()) 