#!/usr/bin/env python3
"""
List session IDs directly from database
"""

import requests
import json

def get_sessions_from_backend():
    """Get session IDs using backend API endpoints"""
    backend_url = "http://localhost:3000"
    
    print("🔍 Getting session IDs from backend...\n")
    
    # Method 1: Check health and active sessions
    try:
        health_response = requests.get(f"{backend_url}/api/health")
        if health_response.status_code == 200:
            health_data = health_response.json()
            print("✅ Backend Health:")
            print(f"   Status: {health_data['status']}")
            print(f"   Active Sessions: {health_data['active_sessions']}")
            print(f"   Supabase: {health_data['services'].get('supabase', 'unknown')}")
        else:
            print("❌ Backend health check failed")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    print("\n" + "="*50)
    
    # Method 2: Try to get conversations list
    try:
        conversations_response = requests.get(f"{backend_url}/api/conversations")
        if conversations_response.status_code == 200:
            conversations = conversations_response.json()
            print("📋 Database Conversations:")
            if conversations:
                for conv in conversations[:5]:  # Show first 5
                    print(f"   • {conv.get('session_id', 'N/A')} ({conv.get('mode', 'unknown')})")
            else:
                print("   No conversations found")
        else:
            error_detail = conversations_response.json().get('detail', 'Unknown error')
            print(f"❌ Conversations query failed: {error_detail}")
    except Exception as e:
        print(f"❌ Conversations error: {e}")
    
    print("\n" + "="*50)
    
    # Method 3: Test specific session IDs
    test_sessions = [
        "session_demo_001",
        "session_test_123", 
        "session_sample_456",
        "session_interview_789"
    ]
    
    print("🧪 Testing Session IDs:")
    for session_id in test_sessions:
        try:
            transcript_response = requests.get(f"{backend_url}/api/transcripts/{session_id}")
            if transcript_response.status_code == 200:
                transcripts = transcript_response.json()
                print(f"   ✅ {session_id}: {len(transcripts)} transcripts found")
            elif transcript_response.status_code == 404:
                print(f"   ❌ {session_id}: No transcripts found")
            else:
                print(f"   ⚠️  {session_id}: Error {transcript_response.status_code}")
        except Exception as e:
            print(f"   ❌ {session_id}: Error - {e}")
    
    print("\n" + "="*50)
    print("📝 How to create test data:")
    print("   1. Start an interview at: http://localhost:3001/interview")
    print("   2. Or restart backend to enable test endpoints")
    print("   3. Use any session ID in transcript viewer to test UI")

if __name__ == "__main__":
    get_sessions_from_backend()