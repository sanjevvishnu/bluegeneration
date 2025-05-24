# 🚀 Live Audio Interview Practice - Supabase Backend

## ✨ **New Simplified Architecture**

**Single Python Backend with Supabase** - No more complex multi-backend setup!

```
React Frontend (port 3001)
    ↓ WebSocket
Python Backend (FastAPI + port 3000)
    ├── Supabase (Database + Real-time)
    ├── Gemini Live API 
    └── ElevenLabs API
```

### **Why This Is Better:**
- ✅ **Single backend** instead of 2 separate servers
- ✅ **Real-time database** with Supabase
- ✅ **Persistent sessions** and transcripts
- ✅ **Scalable architecture** for production
- ✅ **WebSocket instead of Socket.IO** (simpler)
- ✅ **FastAPI** for modern Python web framework

## 🛠️ **Setup Instructions**

### **1. Create Supabase Project**

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Click "New Project"
3. Choose organization and create project
4. Wait for project to be ready

### **2. Setup Database Schema**

1. Go to **SQL Editor** in Supabase Dashboard
2. Copy the contents of `supabase_schema.sql`
3. Paste and run the SQL to create tables

### **3. Get Supabase Credentials**

1. Go to **Settings → API** in Supabase Dashboard
2. Copy the following values:

```bash
Project URL: https://[project-id].supabase.co
anon public key: eyJ... (starts with eyJ)
```

### **4. Configure Environment Variables**

Update your `.env` file:

```bash
# Existing keys
ELEVENLABS_API_KEY=sk_5bcb4cc8adc1f91236a158bdc7f43a9141bfafd476f541b2
GOOGLE_API_KEY=your_actual_gemini_api_key_here

# NEW: Add Supabase configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
```

### **5. Install Dependencies**

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies (for frontend)
npm install
```

### **6. Run the System**

#### **Single Command (Recommended):**
```bash
npm run dev
```

This starts:
- Python FastAPI backend (port 3000)
- React frontend (port 3001)

#### **Manual Start:**
```bash
# Terminal 1: Python Backend
npm run supabase-backend

# Terminal 2: React Frontend  
npm run frontend
```

## 🎯 **How It Works**

### **Recording Flow:**
1. **Frontend**: User clicks record → WebSocket to Python backend
2. **Python Backend**: Processes audio through Gemini Live API
3. **Supabase**: Stores transcript entries in real-time database
4. **Response**: Gemini/ElevenLabs generates voice response
5. **Real-time**: All clients see transcript updates instantly

### **Key Features:**

#### **FastAPI Backend (`supabase_backend.py`)**
- **WebSocket endpoint**: `/ws/{session_id}` for real-time communication
- **REST API**: `/api/health`, `/api/prompts`, `/api/transcripts/{session_id}`
- **Session management**: Automatic cleanup and persistence
- **Error handling**: Graceful fallbacks and detailed logging

#### **Supabase Integration**
- **Database**: PostgreSQL with real-time subscriptions
- **Tables**: `interview_sessions`, `transcripts`
- **Real-time**: Instant transcript updates across all clients
- **Persistence**: All data survives server restarts

#### **React Frontend** 
- **WebSocket client**: Native WebSocket instead of Socket.IO
- **Real-time UI**: Instant transcript updates
- **Audio recording**: MediaRecorder with volume monitoring
- **Voice providers**: Toggle between Gemini and ElevenLabs

## 🔧 **API Endpoints**

### **WebSocket (`/ws/{session_id}`)**
```javascript
// Connect
const ws = new WebSocket('ws://localhost:3000/ws/session123')

// Messages
ws.send(JSON.stringify({
  type: 'create_session',
  data: { mode: 'amazon_interviewer', use_elevenlabs: false }
}))

ws.send(JSON.stringify({
  type: 'audio_data', 
  data: { audio: 'base64-encoded-audio' }
}))

ws.send(JSON.stringify({
  type: 'text_input',
  data: { text: 'Hello, how are you?' }
}))
```

### **REST API**
- `GET /api/health` - System health check
- `GET /api/prompts` - Get interview prompts
- `GET /api/transcripts/{session_id}` - Get session transcript
- `DELETE /api/sessions/{session_id}` - Delete session

## 🗄️ **Database Schema**

### **interview_sessions**
```sql
id              UUID PRIMARY KEY
session_id      TEXT UNIQUE NOT NULL
mode           TEXT NOT NULL  
use_elevenlabs BOOLEAN DEFAULT FALSE
created_at     TIMESTAMP WITH TIME ZONE
updated_at     TIMESTAMP WITH TIME ZONE
status         TEXT DEFAULT 'active'
```

### **transcripts**
```sql
id         UUID PRIMARY KEY
session_id TEXT NOT NULL
speaker    TEXT NOT NULL ('User' | 'Assistant')
text       TEXT NOT NULL
provider   TEXT (gemini | elevenlabs | user | text)
timestamp  TIMESTAMP WITH TIME ZONE
```

## 🔍 **Troubleshooting**

### **"Supabase not configured"**
- Check `SUPABASE_URL` and `SUPABASE_ANON_KEY` in `.env`
- Verify project URL format: `https://[project-id].supabase.co`
- Ensure anon key starts with `eyJ`

### **"Failed to connect WebSocket"**
- Python backend not running on port 3000
- Check console: `python supabase_backend.py`
- Verify no port conflicts

### **"Table doesn't exist"**
- Run `supabase_schema.sql` in Supabase SQL Editor
- Check tables exist in Database → Tables

### **Recording fails**
- Microphone permissions in browser
- Check backend logs for Gemini/ElevenLabs errors
- Verify API keys in `.env`

## 🚀 **Production Deployment**

### **Build Frontend**
```bash
npm run build
```

### **Deploy Backend**
```bash
# Set environment variables
export NODE_ENV=production
export SUPABASE_URL=your-url
export SUPABASE_ANON_KEY=your-key
export GOOGLE_API_KEY=your-key
export ELEVENLABS_API_KEY=your-key

# Start production server
npm start
```

The production server serves both the React app and API on a single port.

## 📊 **Migration from Old System**

If you were using the old Node.js + Python backend setup:

### **What Changed:**
- ❌ **Removed**: Node.js server (`server.js`)
- ❌ **Removed**: Socket.IO dependency
- ❌ **Removed**: Separate Python backend (`python_backend.py`)
- ✅ **Added**: Single FastAPI backend (`supabase_backend.py`)
- ✅ **Added**: Supabase database integration
- ✅ **Added**: WebSocket communication

### **Benefits:**
- 🔥 **50% fewer moving parts** (1 backend vs 2)
- 🗄️ **Persistent data** (database vs in-memory)
- ⚡ **Real-time updates** (Supabase vs manual broadcast)
- 🚀 **Production-ready** (database + scaling)

## 🎤 **Voice Providers**

### **Gemini Voice (Default)**
- Built-in Gemini Live API voice
- Lower latency
- Integrated transcription

### **ElevenLabs Voice**  
- Higher quality synthesis
- More natural sounding
- Rachel voice (configurable)

## 📝 **Development Notes**

- **Backend**: Python 3.11+ + FastAPI + Supabase + Uvicorn
- **Frontend**: Next.js 15 + React 19 + TypeScript + Tailwind + shadcn/ui
- **Database**: PostgreSQL (via Supabase)
- **Real-time**: Supabase real-time subscriptions + WebSocket
- **Audio**: Web Audio API + MediaRecorder
- **AI**: Gemini Live API + ElevenLabs API

The system is now production-ready with a clean, scalable architecture! 🎉 