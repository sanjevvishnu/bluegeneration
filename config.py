#!/usr/bin/env python3
"""
Configuration for Live Audio Interview Practice
Centralizes all environment variables and settings
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # API Keys
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
    
    # Supabase
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
    
    # Server Settings
    PORT = int(os.getenv('PORT', 3000))
    HOST = os.getenv('HOST', '0.0.0.0')
    NODE_ENV = os.getenv('NODE_ENV', 'development')
    
    # Gemini Settings
    GEMINI_MODEL = "gemini-2.0-flash-live-001"
    
    # Audio Settings
    AUDIO_SAMPLE_RATE = 16000
    AUDIO_CHANNELS = 1
    AUDIO_FORMAT = "pcm"
    AUDIO_MIME_TYPE = "audio/pcm;rate=16000"
    
    # Session Settings
    MAX_SESSION_DURATION = 900  # 15 minutes
    MAX_CONCURRENT_SESSIONS = 10
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required = ['GOOGLE_API_KEY', 'SUPABASE_URL', 'SUPABASE_ANON_KEY']
        missing = [key for key in required if not getattr(cls, key)]
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        return True
    
    @classmethod
    def is_development(cls):
        """Check if running in development mode"""
        return cls.NODE_ENV == 'development'

# Global config instance
config = Config() 