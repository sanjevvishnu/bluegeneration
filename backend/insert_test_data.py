#!/usr/bin/env python3
"""
Insert test transcript data directly into Supabase using the same connection as the backend
"""

import os
import sys
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Add the backend directory to Python path to import backend modules
sys.path.append('/Users/sanjevvishnuthulasiraman/Downloads/bluegeneration/backend')

# Load environment variables
load_dotenv()

try:
    from supabase import create_client, Client
    
    def insert_test_data():
        """Insert test conversation and transcript data"""
        
        # Initialize Supabase client
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not supabase_url or not supabase_key:
            print("❌ Missing Supabase credentials")
            return None
            
        try:
            supabase: Client = create_client(supabase_url, supabase_key)
            print("✅ Connected to Supabase")
            
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
            
            print(f"📋 Creating conversation: {test_session_id}")
            conv_result = supabase.table("conversations").insert(conversation_data).execute()
            
            if conv_result.data:
                print("✅ Conversation created successfully")
                
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
                
                print(f"📝 Creating {len(test_transcripts)} transcript entries...")
                
                for i, transcript in enumerate(test_transcripts):
                    result = supabase.table("transcripts").insert(transcript).execute()
                    if result.data:
                        speaker_icon = "🤖" if transcript["speaker"] == "assistant" else "👨‍💻"
                        print(f"  {i+1}. {speaker_icon} {transcript['speaker'].title()}: {transcript['text'][:60]}...")
                    else:
                        print(f"  ❌ Failed to insert transcript {i+1}")
                
                print(f"\n🎯 Test data created successfully!")
                print(f"📋 Session ID: {test_session_id}")
                print(f"\n🌐 Test in frontend:")
                print(f"   1. Go to: http://localhost:3001/dashboard")
                print(f"   2. Click 'Transcripts' in sidebar")
                print(f"   3. Enter session ID: {test_session_id}")
                print(f"   4. Click 'Load Transcript'")
                
                return test_session_id
                
            else:
                print("❌ Failed to create conversation")
                return None
                
        except Exception as e:
            print(f"❌ Database error: {e}")
            return None
            
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please make sure supabase-py is installed: pip install supabase")

if __name__ == "__main__":
    insert_test_data()