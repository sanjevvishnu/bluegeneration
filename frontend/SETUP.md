# Coimbatore Frontend - Setup Guide

## 🎯 **Overview**
This is your **clean, organized frontend** with full backend integration using the same WebSocket approach as the original app.

## 🏗️ **Architecture**
- **Frontend**: Clean React/Next.js app with organized components
- **Backend**: Python FastAPI server with Gemini Live API integration
- **Communication**: WebSocket connection for real-time audio streaming

## 🚀 **Quick Start**

### **1. Start the Backend**
```bash
# From the main project directory
cd /Users/sanjevvishnuthulasiraman/Downloads/bluegeneration

# Activate virtual environment
source venv/bin/activate

# Start the Python backend
python supabase_backend.py
```
The backend will run on `http://localhost:3000`

### **2. Start the Frontend**
```bash
# From the frontend directory
cd frontend

# Install dependencies (if not done)
npm install

# Start the frontend
npm run dev
```
The frontend will run on `http://localhost:3001`

## 🔧 **How the Integration Works**

### **Backend Connection**
- **WebSocket URL**: `ws://localhost:3000/ws/{session_id}`
- **Audio Format**: 16kHz mono PCM input, 24kHz output
- **Message Types**:
  - `create_session` - Initialize interview session
  - `start_audio` - Begin recording
  - `audio_data` - Stream audio chunks
  - `stop_audio` - Stop recording
  - `transcript_update` - Receive AI responses

### **Frontend Components**
1. **InterviewCard**: Clean cards showing interview prompts
2. **InterviewSession**: Full interview interface with:
   - Real-time WebSocket connection
   - Audio recording with volume meter
   - Live transcript display
   - Connection status monitoring
   - Error handling and retry

### **Custom Hook** (`useInterviewSession`)
- Manages WebSocket connection
- Handles audio recording/playback
- Processes transcript updates
- Provides clean interface for components

## 🎨 **UI Features**
- **Clean Design**: Modern cards and layout
- **Real-time Status**: Connection, recording, and session status
- **Volume Meter**: Visual feedback for microphone input
- **Error Handling**: Clear error messages and retry options
- **Responsive**: Works on desktop and mobile

## 📋 **Usage Instructions**

1. **Start Backend**: Run `python supabase_backend.py`
2. **Start Frontend**: Run `npm run dev` in frontend directory
3. **Select Interview**: Choose from Google, Amazon, Microsoft, or Startup
4. **Connect**: Click "Connect to Interview System"
5. **Record**: Click microphone button to start/stop recording
6. **Converse**: Speak naturally with the AI interviewer
7. **End**: Click "End Interview" when finished

## 🔑 **Environment Setup**

Make sure you have these environment variables in your `.env` file:
```bash
GOOGLE_API_KEY=your_google_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_key_here  # Optional
SUPABASE_URL=your_supabase_url  # Optional
SUPABASE_ANON_KEY=your_supabase_key  # Optional
```

## 🐛 **Troubleshooting**

### **Backend Not Connecting**
- Ensure backend is running on port 3000
- Check environment variables are set
- Verify Google API key is valid

### **Audio Issues**
- Allow microphone access in browser
- Use headphones to prevent feedback
- Check browser audio permissions

### **WebSocket Errors**
- Restart backend server
- Clear browser cache
- Check firewall settings

## 🎯 **Key Benefits**

✅ **Clean Architecture**: Well-organized, maintainable code
✅ **Type Safety**: Full TypeScript integration
✅ **Real-time Audio**: Seamless voice conversation
✅ **Error Handling**: Robust connection management
✅ **Modern UI**: Beautiful, responsive interface
✅ **Backend Integration**: Same proven WebSocket approach

This setup gives you the **best of both worlds**: clean, organized frontend code with the powerful backend integration from the original app! 