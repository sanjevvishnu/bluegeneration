#!/usr/bin/env python3
"""
Simple script to get session IDs from Supabase for testing transcripts
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def get_session_ids():
    """Get session IDs from Supabase tables"""
    
    # Initialize Supabase client
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials in .env file")
        return
    
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Connected to Supabase")
        
        # Query conversations table for session IDs
        print("\n📋 Checking conversations table...")
        conversations_response = supabase.table("conversations").select("id, session_id, mode, status, created_at").limit(10).execute()
        
        if conversations_response.data:
            print(f"Found {len(conversations_response.data)} conversations:")
            for conv in conversations_response.data:
                print(f"  • Session ID: {conv['session_id']}")
                print(f"    Mode: {conv['mode']}, Status: {conv['status']}")
                print(f"    Created: {conv['created_at']}")
                print()
        else:
            print("  No conversations found")
        
        # Query transcripts table for session IDs
        print("\n📝 Checking transcripts table...")
        transcripts_response = supabase.table("transcripts").select("session_id").limit(10).execute()
        
        if transcripts_response.data:
            # Get unique session IDs from transcripts
            session_ids = list(set([t['session_id'] for t in transcripts_response.data if t['session_id']]))
            print(f"Found {len(session_ids)} unique session IDs with transcripts:")
            for session_id in session_ids[:5]:  # Show first 5
                print(f"  • {session_id}")
        else:
            print("  No transcripts found")
            
        # If no data exists, create a sample conversation and transcript
        if not conversations_response.data and not transcripts_response.data:
            print("\n🔨 Creating sample data for testing...")
            
            sample_session_id = f"session_{uuid.uuid4().hex[:8]}"
            
            # Create sample conversation
            conv_data = {
                "session_id": sample_session_id,
                "mode": "technical_screening",
                "status": "completed",
                "title": "Sample Technical Interview",
                "duration": 300,
                "performance_score": 8.5,
                "difficulty_level": "medium"
            }
            
            supabase.table("conversations").insert(conv_data).execute()
            
            # Create sample transcripts
            sample_transcripts = [
                {
                    "session_id": sample_session_id,
                    "speaker": "assistant",
                    "text": "Hello! I'm here to conduct your technical interview today. Let's start with a simple question: Can you explain what a hash table is?",
                    "provider": "gemini_text",
                    "confidence_score": 0.95
                },
                {
                    "session_id": sample_session_id,
                    "speaker": "user", 
                    "text": "A hash table is a data structure that implements an associative array, using a hash function to compute an index for storing key-value pairs.",
                    "provider": "user_input",
                    "confidence_score": 1.0
                },
                {
                    "session_id": sample_session_id,
                    "speaker": "assistant",
                    "text": "Excellent! That's a great definition. Now, can you tell me about the time complexity of hash table operations?",
                    "provider": "gemini_text", 
                    "confidence_score": 0.98
                },
                {
                    "session_id": sample_session_id,
                    "speaker": "user",
                    "text": "Hash table operations like insertion, deletion, and lookup typically have O(1) average time complexity, but can degrade to O(n) in the worst case when there are many collisions.",
                    "provider": "user_input",
                    "confidence_score": 1.0
                }
            ]
            
            for transcript in sample_transcripts:
                supabase.table("transcripts").insert(transcript).execute()
            
            print(f"✅ Created sample data with session ID: {sample_session_id}")
            print(f"\n🎯 You can test the frontend with this session ID: {sample_session_id}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    import uuid
    import traceback
    get_session_ids()