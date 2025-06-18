# 🚀 Simple Supabase Backend - Coimbatore

## 🐍 **Python Setup (Required)**

### **1. Create Virtual Environment**
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Verify activation (should show venv path)
which python
```

### **2. Install Dependencies**
```bash
# With virtual environment activated
pip install -r requirements.txt
```

### **3. Run Backend**
```bash
# Make sure virtual environment is activated
python simple_supabase_backend.py
```

**⚠️ Important**: Always activate the virtual environment before running the backend or installing packages.

## ✨ **Simplified Architecture**

**Two-Table Design with Supabase** - Clean and minimal!

```
React Frontend (port 3001)
    ↓ WebSocket + REST API
Python Backend (FastAPI + port 3000)
    ├── Supabase (2 tables only)
    │   ├── conversations
    │   └── transcripts
    └── Gemini Live API 
```

### **Why This Simplified Version:**
- ✅ **Just 2 tables** instead of complex schema
- ✅ **Minimal setup** - faster to get started
- ✅ **Core functionality** - conversations + transcripts
- ✅ **Real-time updates** with Supabase
- ✅ **Easy to understand** and extend

## 🗄️ **Database Schema (2 Tables Only)**

### **1. conversations**
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT UNIQUE NOT NULL,
    title TEXT,
    mode TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    duration INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'
);
```

### **2. transcripts**
```sql
CREATE TABLE transcripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    session_id TEXT NOT NULL,
    speaker TEXT NOT NULL, -- 'User' or 'Assistant'
    text TEXT NOT NULL,
    provider TEXT, -- gemini, user, text
    audio_url TEXT,
    confidence_score FLOAT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sequence_number INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'
);
```

## 🛠️ **Setup Instructions**

### **1. Create Supabase Project**
1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Click "New Project"
3. Choose organization and create project
4. Wait for project to be ready

### **2. Setup Database Schema**
1. Go to **SQL Editor** in Supabase Dashboard
2. Copy the contents of `supabase_schema_simple.sql`
3. Paste and run the SQL to create tables

### **3. Get Supabase Credentials**
1. Go to **Settings → API** in Supabase Dashboard
2. Copy these values:

```bash
Project URL: https://[project-id].supabase.co
anon public key: eyJ... (starts with eyJ)
```

### **4. Configure Environment Variables**
Update your `.env` file:

```bash
# AI API Keys
GOOGLE_API_KEY=your_gemini_api_key_here

# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
```

### **5. Install Dependencies**
```bash
# Install Python dependencies
pip install -r requirements.txt
```

### **6. Run the Simple Backend**
```bash
# Start the simple Supabase backend
python simple_supabase_backend.py
```

The backend will start on `http://localhost:3000`

## 🔌 **API Endpoints**

### **WebSocket (`/ws/{session_id}`)**
```javascript
// Connect
const ws = new WebSocket('ws://localhost:3000/ws/session123')

// Create session
ws.send(JSON.stringify({
  type: 'create_session',
  data: { 
    mode: 'amazon_interviewer'
  }
}))

// Send audio
ws.send(JSON.stringify({
  type: 'audio_data', 
  data: { audio: 'base64-encoded-audio' }
}))

// Send text
ws.send(JSON.stringify({
  type: 'text_input',
  data: { text: 'Hello, how are you?' }
}))

// End session
ws.send(JSON.stringify({
  type: 'end_session',
  data: {}
}))
```

### **REST API**
- `GET /api/health` - System health check
- `GET /api/prompts` - Get interview prompts
- `GET /api/conversations` - List all conversations
- `GET /api/conversations/{session_id}` - Get conversation + transcripts
- `DELETE /api/conversations/{session_id}` - Delete conversation

## 📊 **Data Flow**

### **1. Create Session**
```
Frontend → WebSocket → Backend
Backend → Supabase (conversations table)
Backend → Gemini Live API (create session)
```

### **2. Audio Processing**
```
Frontend → WebSocket (audio) → Backend
Backend → Gemini Live API → AI Response
Backend → Supabase (transcripts table)
Backend → WebSocket → Frontend
```

### **3. Real-time Updates**
```
Supabase → Real-time subscriptions → Backend
Backend → WebSocket → All connected clients
```

## 🎯 **Features**

### **Core Features**
- ✅ **Real-time audio interviews** with Gemini Live API
- ✅ **Live transcript storage** in Supabase
- ✅ **Session management** with automatic cleanup
- ✅ **WebSocket communication** for real-time updates
- ✅ **REST API** for data access

### **Database Features**
- ✅ **Automatic sequence numbering** for transcripts
- ✅ **Cascade deletion** (delete conversation → delete transcripts)
- ✅ **Full-text search** on transcript content
- ✅ **Real-time subscriptions** for live updates
- ✅ **JSONB metadata** for flexible data storage

### **AI Integration**
- ✅ **Gemini Live API** for real-time audio processing
- ✅ **Multiple interview modes** (Amazon, Google, etc.)
- ✅ **Configurable system instructions**

## 🔧 **Configuration**

### **Interview Modes**
Configure in `prompts.json`:
```json
{
  "amazon_interviewer": {
    "name": "Amazon Technical Interviewer",
    "system_instruction": "You are a senior software engineer...",
    "welcome_message": "🚀 Amazon Interview Mode",
    "description": "📦 Amazon Interview Mode: Technical + Leadership"
  }
}
```

## 🚀 **Usage Examples**

### **Start a Session**
```python
# WebSocket message
{
  "type": "create_session",
  "data": {
    "mode": "amazon_interviewer"
  }
}
```

### **Get Conversation Data**
```bash
# REST API call
curl http://localhost:3000/api/conversations/session123
```

### **List All Conversations**
```bash
curl http://localhost:3000/api/conversations
```

## 🔍 **Troubleshooting**

### **"Supabase not configured"**
- Check `SUPABASE_URL` and `SUPABASE_ANON_KEY` in `.env`
- Verify project URL format: `https://[project-id].supabase.co`

### **"No conversation found"**
- Ensure session was created with `create_session` message
- Check Supabase dashboard for data

### **"Gemini client not available"**
- Verify `GOOGLE_API_KEY` in `.env`
- Install: `pip install google-genai`

### **Audio processing fails**
- Check microphone permissions in browser
- Verify Gemini API key is valid
- Check backend logs for detailed errors

## 📈 **Monitoring**

### **Health Check**
```bash
curl http://localhost:3000/api/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "supabase": "connected",
    "gemini": "available"
  },
  "active_sessions": 2
}
```

### **Database Monitoring**
- Check Supabase Dashboard → Database → Tables
- Monitor real-time subscriptions
- View logs in Supabase Dashboard → Logs

## 🎯 **Next Steps**

### **Extend the Schema**
- Add `users` table for authentication
- Add `session_analytics` for metrics
- Add `feedback` table for ratings

### **Add Features**
- User authentication with Supabase Auth
- Session recording and playback
- Performance analytics
- Multi-language support

### **Production Deployment**
- Deploy to Railway/Render/Fly.io
- Setup environment variables
- Configure CORS for production domain
- Add rate limiting and security

This simplified backend provides a solid foundation for your Coimbatore App with minimal complexity and maximum functionality! 