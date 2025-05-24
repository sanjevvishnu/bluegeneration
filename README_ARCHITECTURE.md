# Live Audio Interview Practice - Architecture v2.0

## 🏗️ **Modular Architecture Overview**

This system has been completely redesigned into a **clean, modular architecture** based on [official Gemini Live API documentation](https://ai.google.dev/gemini-api/docs/live) and [working cookbook examples](https://github.com/google-gemini/cookbook/blob/main/quickstarts/Get_started_LiveAPI.py).

### 📁 **File Structure**

```
📁 live-audio-backend/
├── 📄 main.py                    # FastAPI app entry point & coordination
├── 📄 config.py                  # Configuration & environment management
├── 📄 models.py                  # Data structures & types
├── 📄 gemini_live_client.py      # Dedicated Gemini Live API handler  
├── 📄 audio_processor.py         # Audio format conversion & validation
├── 📄 session_manager.py         # Session state & lifecycle management
├── 📄 supabase_client.py         # Database operations & real-time
└── 📄 requirements.txt           # Dependencies
```

---

## 🔧 **Component Architecture**

### 1. **main.py** - Application Coordinator
- **FastAPI application** with proper lifespan management
- **WebSocket handling** for real-time communication
- **Component coordination** between all modules
- **Error handling** and graceful shutdown
- **HTTP API endpoints** for health, transcripts, etc.

### 2. **config.py** - Configuration Management
- **Centralized environment variables** from `.env`
- **Configuration validation** on startup
- **Default values** and environment detection
- **Type-safe configuration** access

### 3. **models.py** - Data Structures
- **Typed data classes** for all system entities
- **Enums** for modes, message types, response modalities
- **Validation** and serialization helpers
- **Clear separation** of concerns

### 4. **gemini_live_client.py** - Gemini Integration
- **Based on official cookbook examples**
- **Proper async context management** for Live API
- **Separate TEXT and AUDIO processing** paths
- **Single response modality** per session (as required)
- **Conversation context** building and management
- **Error handling** and fallback strategies

### 5. **audio_processor.py** - Audio Handling
- **Format conversion** to 16-bit PCM at 16kHz mono
- **Audio validation** and error handling
- **WAV and raw PCM** support
- **Resampling** and channel conversion
- **Base64 encoding/decoding** for transport

### 6. **session_manager.py** - Session Management
- **Session lifecycle** management
- **Thread-safe operations** with async locks
- **Session state** persistence
- **Cleanup tasks** for expired sessions
- **Statistics** and monitoring

### 7. **supabase_client.py** - Database Operations
- **All database operations** centralized
- **Real-time subscriptions** support
- **Transaction handling** and error recovery
- **Connection testing** and health checks
- **Data model** enforcement

---

## ✅ **Key Improvements from v1.0**

### **1. Fixed Gemini Live API Integration**
```python
# OLD (Broken)
session = await self.gemini_client.aio.live.connect()  # Wrong pattern

# NEW (Correct)
async with self.gemini_client.aio.live.connect(
    model=config.GEMINI_MODEL, 
    config=live_config
) as session:
    # Proper async context manager
```

### **2. Single Response Modality per Session**
- **TEXT mode**: Uses standard Gemini API for text conversations
- **AUDIO mode**: Uses Live API with proper audio format
- **No mixed modalities** in same session (as per API requirements)

### **3. Proper Audio Format**
```python
# Correct format for Gemini Live API
audio_blob = Blob(
    data=audio_data.data,
    mime_type="audio/pcm;rate=16000"  # Required format
)
```

### **4. Conversation Context Management**
- **History-aware responses** prevent repetition
- **Role separation** prevents AI generating both sides
- **Context building** with proper conversation structure

### **5. Thread-Safe Session Management**
- **Async locks** per session
- **Race condition** prevention
- **Proper cleanup** and resource management

---

## 🔄 **Data Flow Architecture**

### **Text Input Flow**
```
Frontend → WebSocket → main.py → session_manager
    ↓
gemini_live_client (TEXT mode) → supabase_client
    ↓
Response → WebSocket → Frontend
```

### **Audio Input Flow**
```
Frontend → WebSocket → main.py → audio_processor
    ↓
gemini_live_client (AUDIO mode) → supabase_client
    ↓
Audio/Text Response → WebSocket → Frontend
```

### **Session Management Flow**
```
Create Session → session_manager → supabase_client
    ↓
Active Session → Locks & State → Cleanup Tasks
```

---

## 🚀 **API Endpoints**

### **HTTP Endpoints**
- `GET /` - System status and component health
- `GET /api/health` - Detailed health check with statistics
- `GET /api/prompts` - Available interview modes
- `GET /api/transcripts/{session_id}` - Session transcript
- `DELETE /api/sessions/{session_id}` - Delete session data

### **WebSocket Messages**
- `create_session` - Initialize new interview session
- `text_input` - Send text message
- `audio_data` - Send audio data
- `switch_mode` - Change interview mode
- `switch_voice` - Toggle ElevenLabs TTS

---

## 🔐 **Configuration Requirements**

### **Environment Variables (.env)**
```bash
# Required
GOOGLE_API_KEY=your_gemini_api_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key

# Optional
ELEVENLABS_API_KEY=your_elevenlabs_key
PORT=3000
HOST=0.0.0.0
NODE_ENV=development
```

---

## 📊 **Database Schema**

### **interview_sessions Table**
```sql
CREATE TABLE interview_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT UNIQUE NOT NULL,
    mode TEXT NOT NULL,
    use_elevenlabs BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'active'
);
```

### **transcripts Table**
```sql
CREATE TABLE transcripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NOT NULL,
    speaker TEXT NOT NULL,
    text TEXT NOT NULL,
    provider TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (session_id) REFERENCES interview_sessions(session_id)
);
```

---

## 🛠️ **Development & Deployment**

### **Local Development**
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Run backend
python main.py
```

### **Testing**
```bash
# Health check
curl http://localhost:3000/api/health

# WebSocket test
wscat -c ws://localhost:3000/ws/test-session
```

### **Production Deployment**
- Set `NODE_ENV=production`
- Use proper secrets management
- Configure load balancing for WebSockets
- Monitor session cleanup and resource usage

---

## 🔍 **Monitoring & Debugging**

### **Built-in Monitoring**
- Component health status
- Session statistics
- Database connection status
- Real-time metrics

### **Debugging Tools**
- Detailed error logging
- WebSocket message tracing
- Audio format validation
- Configuration validation

---

## 🎯 **Benefits of New Architecture**

1. **✅ Modularity**: Each component has single responsibility
2. **✅ Testability**: Components can be tested independently
3. **✅ Maintainability**: Clear separation makes debugging easier
4. **✅ Scalability**: Components can be scaled individually
5. **✅ Reliability**: Proper error handling and fallbacks
6. **✅ Standards Compliance**: Follows official API documentation

This architecture provides a **solid foundation** for the Live Audio Interview Practice system with **proper Gemini Live API integration** and **production-ready design patterns**. 