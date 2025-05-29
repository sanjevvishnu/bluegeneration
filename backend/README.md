# 🔧 Backend Directory

This directory contains all backend-related files for the AI Interview Practice App.

## 📁 **File Structure**

### **Main Servers**
- `websocket_server.py` - **Primary WebSocket server** with Gemini Live API integration
- `main.py` - FastAPI-based backend with WebSocket support  
- `supabase_backend.py` - Supabase-integrated backend implementation

### **Core Modules**
- `config.py` - Configuration management
- `models.py` - Data models and types
- `session_manager.py` - Session lifecycle management
- `audio_processor.py` - Audio processing utilities
- `supabase_client.py` - Supabase database client

### **API Integration**
- `google_cookbook_live_api.py` - Google Gemini Live API implementation
- `official_cookbook.py` - Official Google cookbook examples
- `quick_voice_test.py` - Voice/audio testing utilities

### **Data & Config**
- `prompts.json` - Interview prompts and questions
- `requirements.txt` - Python dependencies
- `railway.json` - Railway deployment configuration
- `supabase_schema.sql` - Database schema

## 🚀 **Quick Start**

### **1. Install Dependencies**
```bash
cd backend
pip install -r requirements.txt
```

### **2. Set Environment Variables**
```bash
export GOOGLE_API_KEY="your_gemini_api_key_here"
```

### **3. Run the WebSocket Server**
```bash
python websocket_server.py
```

Server will start on `ws://localhost:8765`

## 🔧 **Available Backends**

### **Option A: WebSocket Server (Recommended)**
```bash
python websocket_server.py
```
- ✅ Real-time audio streaming
- ✅ Gemini Live API integration
- ✅ Voice Activity Detection (VAD)
- ✅ Production ready

### **Option B: FastAPI Backend**
```bash
python main.py
```
- ✅ RESTful API endpoints
- ✅ WebSocket support
- ✅ Session management
- ✅ Supabase integration

### **Option C: Supabase Backend**
```bash
python supabase_backend.py
```
- ✅ Database persistence
- ✅ User management
- ✅ Session history
- ✅ Analytics

## 🌐 **Deployment**

### **Railway (Recommended)**
```bash
# Deploy directly from this directory
railway deploy
```

### **Render/Heroku**
- Use `requirements.txt` for dependencies
- Set start command: `python websocket_server.py`
- Configure environment variables

## 🔑 **Required Environment Variables**

```bash
GOOGLE_API_KEY=your_gemini_api_key_here
PORT=8765  # Optional, defaults to 8765
HOST=0.0.0.0  # Optional, defaults to 0.0.0.0
```

## 📊 **Testing**

```bash
# Test voice/audio functionality
python quick_voice_test.py

# Test Google API integration
python google_cookbook_live_api.py
```

## 🎯 **Integration with Frontend**

The frontend expects the WebSocket server at:
- **Development**: `ws://localhost:8765`
- **Production**: Set via `NEXT_PUBLIC_WS_URL` environment variable

See `../DEPLOYMENT.md` for complete deployment instructions. 