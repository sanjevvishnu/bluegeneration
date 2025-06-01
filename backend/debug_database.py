#!/usr/bin/env python3
"""
Database Diagnostic Script
Check the current state of Supabase tables and permissions
"""

import os
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime

# Load environment variables
load_dotenv()

def main():
    print("🔍 Database Diagnostic Script")
    print("=" * 50)
    
    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env file")
        return
    
    print(f"🔗 Connecting to: {supabase_url}")
    
    try:
        # Initialize Supabase client
        supabase = create_client(supabase_url, supabase_key)
        print("✅ Supabase client initialized")
        
        # Test 1: Check conversations table
        print("\n📋 Testing conversations table...")
        conversations = supabase.table('conversations').select('*').limit(5).execute()
        print(f"✅ Found {len(conversations.data)} conversations")
        
        for conv in conversations.data:
            print(f"  - {conv['session_id']} ({conv['mode']}) - {conv['status']} - {conv.get('created_at', 'No timestamp')}")
        
        # Test 2: Check transcripts table
        print("\n📝 Testing transcripts table...")
        transcripts = supabase.table('transcripts').select('*').limit(5).execute()
        print(f"✅ Found {len(transcripts.data)} transcripts")
        
        for trans in transcripts.data:
            print(f"  - {trans['session_id']} ({trans['speaker']}): {trans['text'][:50]}...")
        
        # Test 3: Check users table
        print("\n👤 Testing users table...")
        users = supabase.table('users').select('*').limit(5).execute()
        print(f"✅ Found {len(users.data)} users")
        
        for user in users.data:
            print(f"  - {user.get('email', 'No email')} ({user.get('full_name', 'No name')})")
        
        # Test 4: Try creating a test conversation
        print("\n🧪 Testing conversation creation...")
        test_session_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        test_data = {
            'session_id': test_session_id,
            'mode': 'test_interviewer',
            'status': 'active',
            'title': f"Test conversation - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        }
        
        result = supabase.table('conversations').insert(test_data).execute()
        if result.data:
            print(f"✅ Successfully created test conversation: {result.data[0]['id']}")
            
            # Test 5: Try creating a test transcript
            print("\n🧪 Testing transcript creation...")
            transcript_data = {
                'conversation_id': result.data[0]['id'],
                'session_id': test_session_id,
                'speaker': 'Test',
                'text': 'This is a test transcript entry',
                'provider': 'test'
            }
            
            transcript_result = supabase.table('transcripts').insert(transcript_data).execute()
            if transcript_result.data:
                print(f"✅ Successfully created test transcript: {transcript_result.data[0]['id']}")
            else:
                print("❌ Failed to create test transcript")
            
            # Clean up test data
            print("\n🧹 Cleaning up test data...")
            supabase.table('conversations').delete().eq('session_id', test_session_id).execute()
            print("✅ Test data cleaned up")
        else:
            print("❌ Failed to create test conversation")
        
        print("\n✅ Database diagnostic complete!")
        
    except Exception as e:
        print(f"❌ Database diagnostic failed: {e}")
        import traceback
        print(f"🔍 Full traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    main() 