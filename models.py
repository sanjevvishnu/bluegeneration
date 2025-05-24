#!/usr/bin/env python3
"""
Data models and types for Live Audio Interview Practice
"""

from typing import Dict, Any, Optional, List, Literal
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class SessionMode(str, Enum):
    """Interview session modes"""
    AMAZON_INTERVIEWER = "amazon_interviewer"
    GOOGLE_INTERVIEWER = "google_interviewer"
    TECHNICAL_INTERVIEW = "technical_interview"

class ResponseModality(str, Enum):
    """Gemini Live API response modalities"""
    TEXT = "TEXT"
    AUDIO = "AUDIO"

class MessageType(str, Enum):
    """WebSocket message types"""
    # Session management
    CREATE_SESSION = "create_session"
    SESSION_CREATED = "session_created"
    SESSION_READY = "session_ready"
    
    # Audio session management (Live API)
    START_AUDIO = "start_audio"
    STOP_AUDIO = "stop_audio"
    AUDIO_STARTED = "audio_started"
    AUDIO_STOPPED = "audio_stopped"
    
    # Communication
    TEXT_INPUT = "text_input"
    AUDIO_DATA = "audio_data"
    AUDIO_CHUNK = "audio_chunk"
    AUDIO_RESPONSE = "audio_response"
    TRANSCRIPT_UPDATE = "transcript_update"
    
    # Control
    SWITCH_MODE = "switch_mode"
    SWITCH_VOICE = "switch_voice"
    MODE_SWITCHED = "mode_switched"
    VOICE_SWITCHED = "voice_switched"
    
    # Status
    ERROR = "error"
    STATUS = "status"

@dataclass
class SessionInfo:
    """Session information"""
    session_id: str
    mode: SessionMode
    response_modality: ResponseModality
    use_elevenlabs: bool = False
    system_instruction: str = ""
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class TranscriptEntry:
    """Transcript entry"""
    session_id: str
    speaker: str
    text: str
    provider: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class AudioData:
    """Audio data container"""
    data: bytes
    sample_rate: int = 16000
    channels: int = 1
    format: str = "pcm"
    
    @property
    def mime_type(self) -> str:
        return f"audio/{self.format};rate={self.sample_rate}"

@dataclass
class WebSocketMessage:
    """WebSocket message container"""
    type: MessageType
    data: Dict[str, Any]
    session_id: Optional[str] = None

@dataclass
class GeminiResponse:
    """Gemini API response"""
    type: Literal["text", "audio"]
    data: str
    provider: str = "gemini"

@dataclass
class ElevenLabsResponse:
    """ElevenLabs TTS response"""
    type: Literal["audio"] = "audio"
    data: str = ""  # base64 encoded audio
    provider: str = "elevenlabs"

# Interview prompts structure
InterviewPrompts = Dict[str, Dict[str, str]] 