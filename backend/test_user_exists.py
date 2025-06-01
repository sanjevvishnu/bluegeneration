#!/usr/bin/env python3
"""
Test script to check if users exist in Supabase database
"""

import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def main():
    print("🔍 Testing User Existence in Supabase Database")
    
    # Initialize Supabase client
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ SUPABASE_URL and SUPABASE_ANON_KEY must be set")
        return
    
    supabase = create_client(supabase_url, supabase_key)
    print("✅ Connected to Supabase")
    
    # Check all users in database
    print("\n📋 All users in database:")
    try:
        users = supabase.table('users').select('clerk_user_id, email, full_name').execute()
        
        if users.data:
            for i, user in enumerate(users.data, 1):
                print(f"  {i}. Clerk ID: {user.get('clerk_user_id', 'N/A')}")
                print(f"     Email: {user.get('email', 'N/A')}")
                print(f"     Name: {user.get('full_name', 'N/A')}")
                print()
        else:
            print("  No users found in database")
            
    except Exception as e:
        print(f"❌ Error querying users: {e}")
    
    # Test specific Clerk user ID (the one from your error)
    test_clerk_id = "user_2xsFNSG2jfP9qgDjRkkSSZOxh45"
    print(f"\n🔍 Testing specific Clerk ID: {test_clerk_id}")
    
    try:
        user_query = supabase.table('users').select('*').eq('clerk_user_id', test_clerk_id).execute()
        
        if user_query.data:
            user = user_query.data[0]
            print(f"✅ User found!")
            print(f"   UUID: {user['id']}")
            print(f"   Email: {user['email']}")
            print(f"   Name: {user.get('full_name', 'N/A')}")
        else:
            print(f"❌ User with Clerk ID '{test_clerk_id}' not found in database")
            print("   This user needs to be created in the database first")
            
    except Exception as e:
        print(f"❌ Error querying specific user: {e}")

if __name__ == "__main__":
    main() 