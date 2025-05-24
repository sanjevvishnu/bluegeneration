# AI Interview Practice App

A real-time AI-powered interview practice application built with Next.js, shadcn/ui, and Google's Gemini Live API. Practice interviews with AI interviewers from top tech companies through voice conversations.

## 🚀 Features

- **Real-time Voice Conversations**: Interactive voice-based interviews using Gemini Live API
- **Multiple Interview Modes**: Pre-configured prompts for different company interviewing styles (Google, Amazon, Microsoft, etc.)
- **Modern UI**: Built with Next.js 14 and shadcn/ui components with a sleek black/white theme
- **WebSocket Communication**: Real-time audio streaming between frontend and backend
- **Audio Processing**: Full-duplex audio recording and playback capabilities
- **Session Management**: Track interview sessions and performance
- **Supabase Integration**: Backend database for storing interview data and analytics

## 🛠 Tech Stack

### Frontend (Port 3000)
- **Next.js 14** - React framework
- **shadcn/ui** - Modern component library (converted from HeroUI)
- **Tailwind CSS** - Utility-first CSS framework
- **TypeScript** - Type-safe development
- **WebSocket Client** - Real-time audio communication

### Backend
- **Python 3.12+** - Core backend language
- **WebSocket Server** (Port 8765) - Real-time communication
- **Google Genai SDK** - Gemini Live API integration
- **Supabase** - Database and authentication
- **AsyncIO** - Asynchronous programming

## 📋 Prerequisites

- Node.js 18+ and npm
- Python 3.12+
- Google API Key (for Gemini Live API)
- Supabase account (optional, for data persistence)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd bluegeneration
```

### 2. Set Up Environment Variables

```bash
# Copy and configure environment variables
cp .env.example .env.local

# Add your Google API key
export GOOGLE_API_KEY='your-google-api-key-here'
```

### 3. Install Dependencies

**Frontend Dependencies:**
```bash
npm install
```

**Backend Dependencies:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Start the Application

**Terminal 1 - Start the Frontend:**
```bash
npm run dev
```
The frontend will be available at `http://localhost:3000`

**Terminal 2 - Start the WebSocket Server:**
```bash
source venv/bin/activate  # Activate virtual environment
python websocket_server.py
```
The WebSocket server will run on `ws://localhost:8765`

## 🎯 How to Use

1. **Open the Application**: Navigate to `http://localhost:3000`
2. **Select Interview Type**: Choose from available interview prompts (Google, Amazon, etc.)
3. **Start Interview**: Click "Start Interview" to begin the voice conversation
4. **Practice**: Speak naturally - the AI interviewer will ask questions and respond in real-time
5. **Review**: Use the built-in audio testing features to verify your setup

## 📁 Project Structure

```
bluegeneration/
├── src/                      # Next.js frontend (main app)
│   ├── app/
│   │   ├── page.tsx         # Home page with interview selection
│   │   ├── interview/       # Interview session page
│   │   └── layout.tsx       # Root layout
│   └── components/ui/       # shadcn/ui components
├── frontend/                # Alternative frontend (Supabase-based)
├── websocket_server.py      # Main WebSocket server
├── prompts.json            # Interview prompt configurations
├── requirements.txt        # Python dependencies
├── package.json           # Node.js dependencies
└── README.md              # This file
```

## 🎨 UI Components

The application uses **shadcn/ui** components with a custom black/white theme:

- **Card Components**: Interview selection and session display
- **Button Components**: Interactive controls with proper hover states
- **Select Components**: Dropdown menus for prompt selection
- **Progress Components**: Audio level indicators
- **Badge Components**: Status indicators

## 🔧 Configuration

### Interview Prompts

Edit `prompts.json` to customize interview scenarios:

```json
{
  "google_interviewer": {
    "name": "Google Technical Interviewer",
    "system_instruction": "You are a Google technical interviewer...",
    "description": "Practice coding and system design questions"
  }
}
```

### Audio Settings

The application uses specific audio formats:
- **Input**: 16kHz, mono, 16-bit PCM
- **Output**: 24kHz, mono, 16-bit PCM

## 🚀 Deployment

### Frontend Deployment (Vercel)

```bash
npm run build
# Deploy to Vercel or your preferred platform
```

### Backend Deployment

The WebSocket server can be deployed to any Python-compatible hosting service. Ensure the following:

1. Set environment variables
2. Install dependencies from `requirements.txt`
3. Configure WebSocket port (default: 8765)

## 🔍 Debugging

### Audio Issues

If you can't hear audio responses:

1. Check browser permissions for microphone
2. Verify WebSocket connection in browser console
3. Test audio with the built-in "Test Audio" button
4. Check server logs for audio streaming errors

### Connection Issues

1. Ensure WebSocket server is running on port 8765
2. Check if GOOGLE_API_KEY is properly set
3. Verify network connectivity

## 📝 Development Notes

### Recent Changes

- **Converted from HeroUI to shadcn/ui**: Complete UI component migration
- **Fixed WebSocket Audio Streaming**: Resolved connection state issues
- **Enhanced Error Handling**: Better debugging and error messages
- **Improved Audio Pipeline**: More reliable audio processing

### Known Issues

- Audio latency may vary based on network conditions
- Some browsers may require HTTPS for microphone access in production

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Google Gemini Live API** - For providing the AI conversation capabilities
- **shadcn/ui** - For the beautiful component library
- **Next.js Team** - For the excellent React framework
- **Supabase** - For backend infrastructure

## 📞 Support

If you encounter any issues or have questions:

1. Check the console logs for error messages
2. Ensure all dependencies are properly installed
3. Verify environment variables are set correctly
4. Create an issue in the GitHub repository

---

**Happy interviewing! 🎉**

# 🎤 AI Interview Practice System

A real-time voice-based interview practice system using Google's Gemini Live API. Practice technical interviews with AI interviewers from top tech companies!

## ✨ Features

- 🎯 **Multiple Interview Modes**: Microsoft, Google, Amazon, Startup, and General Practice
- 🗣️ **Real-time Voice Conversation**: Natural speech interaction with AI
- 🎧 **High-Quality Audio**: 16kHz input, 24kHz output with streaming playback
- 🎭 **Role-specific Prompts**: Each interviewer has unique personality and focus areas
- 🔄 **Seamless Audio Streaming**: No overlapping or choppy audio

## 🚀 Quick Start

### 1. Prerequisites
```bash
# Install dependencies
pip install google-genai websockets

# Set your Google API key
export GOOGLE_API_KEY="your_api_key_here"
```

### 2. Start the System
```bash
# Start the WebSocket server
python websocket_server.py

# Open your browser and go to:
# file:///path/to/your/project/index.html
```

### 3. Practice Interview
1. **Select Interview Mode** from the dropdown (Microsoft, Google, etc.)
2. **Click "Start Interview"** to begin the conversation
3. **Speak naturally** - the AI will respond with voice
4. **Use headphones** to prevent audio feedback

## 📁 Project Structure

```
├── index.html              # Landing page with interview mode selection
├── frontend.html           # Main conversation interface
├── websocket_server.py     # WebSocket server handling Gemini Live API
├── prompts.json           # Interview prompts and configurations
└── README.md              # This file
```

## 🎯 Interview Modes

### 🔍 **Google Technical Interviewer**
- Focus: Algorithms, data structures, system design
- Style: Challenging coding problems with optimization follow-ups
- Culture: Google's engineering excellence

### 📦 **Amazon Technical Interviewer** 
- Focus: Technical skills + Leadership Principles
- Style: Direct, results-focused questioning
- Culture: Customer obsession, ownership, innovation

### 🚀 **Microsoft Technical Interviewer**
- Focus: Programming, algorithms, Microsoft technologies
- Style: Professional, thorough technical evaluation
- Culture: Collaboration and growth mindset

### ⚡ **Startup Technical Lead**
- Focus: Full-stack capabilities, adaptability
- Style: Practical problem-solving scenarios
- Culture: Fast-paced, versatile engineering

### 📚 **General Practice**
- Focus: Comprehensive interview preparation
- Style: Mixed technical and behavioral questions
- Culture: Adaptive difficulty based on responses

## 🔧 How It Works

1. **Prompt Selection**: Choose interview mode on landing page
2. **WebSocket Connection**: Frontend connects to Python server
3. **Gemini Configuration**: Server configures AI with selected prompt
4. **Audio Streaming**: Real-time PCM audio exchange
5. **Queue Management**: Smooth audio playback without overlaps

## 🛠️ Technical Details

- **Frontend**: Vanilla HTML/JS with Web Audio API
- **Backend**: Python with WebSockets and Gemini Live API
- **Audio Format**: 16kHz mono PCM input, 24kHz output
- **Communication**: WebSocket for low-latency audio streaming

## 📝 Adding Custom Prompts

Edit `prompts.json` to add new interview modes:

```json
{
  "your_company": {
    "name": "Your Company Interviewer",
    "description": "Custom interview experience", 
    "system_instruction": "You are an interviewer at...",
    "welcome_message": "🏢 Your Company Mode: Custom focus"
  }
}
```

## 🔑 Getting Google API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Set environment variable: `export GOOGLE_API_KEY="your_key"`

## 💡 Tips for Best Experience

- **Use headphones** to prevent audio feedback
- **Speak clearly** for better recognition
- **Allow microphone access** when prompted
- **Good internet connection** for smooth streaming
- **Quiet environment** for best audio quality

## 🔍 Troubleshooting

**No audio playback?**
- Check browser audio permissions
- Ensure headphones/speakers are working
- Look at browser console for errors

**WebSocket connection failed?**
- Ensure server is running on port 8765
- Check firewall settings
- Verify API key is set correctly

**Audio cutting out?**
- Try using Chrome/Firefox
- Check internet connection stability
- Reduce background applications

---

**Ready to ace your next technical interview!** 🎯✨

# 🎤 Live Audio Interview Practice

**AI-powered interview practice with real-time voice conversation using Gemini Live API and ElevenLabs.**

## ✨ **Features**

- 🎯 **Real-time voice conversation** with AI interviewer
- 🗣️ **Multiple interview modes** (Amazon, Google, Microsoft, etc.)
- 🎤 **Live audio recording** with volume monitoring  
- 🔄 **Voice provider switching** (Gemini vs ElevenLabs)
- 📝 **Real-time transcript** with persistent storage
- 🗄️ **Supabase database** for session management
- 🎨 **Modern UI** with shadcn/ui components

## 🏗️ **Architecture**

**Single Python Backend with Supabase** - Clean and scalable!

```
React Frontend (Next.js + shadcn/ui)
    ↓ WebSocket
Python Backend (FastAPI)
    ├── Supabase (Database + Real-time)
    ├── Gemini Live API 
    └── ElevenLabs API
```

## 🚀 **Quick Start**

### **1. Setup Supabase**
1. Create account at [supabase.com](https://supabase.com)
2. Create new project
3. Run SQL from `supabase_schema.sql` in SQL Editor
4. Get Project URL and API key from Settings → API

### **2. Configure Environment**
```bash
# Copy and update .env file
ELEVENLABS_API_KEY=your_elevenlabs_key
GOOGLE_API_KEY=your_gemini_api_key  
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
```

### **3. Install & Run**
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies  
npm install

# Start the system
npm run dev
```

This starts:
- Python FastAPI backend (port 3000)
- React frontend (port 3001)

## 📁 **Project Structure**

```
├── supabase_backend.py      # Main Python backend (FastAPI + WebSocket)
├── supabase_schema.sql      # Database schema for Supabase
├── prompts.json            # Interview prompts and modes
├── requirements.txt        # Python dependencies
├── package.json           # Node.js scripts and dependencies
├── frontend/              # Next.js React app with shadcn/ui
│   ├── src/components/    # React components
│   └── src/app/          # Next.js app router
└── README_SUPABASE.md    # Detailed setup guide
```

## 🎯 **Usage**

1. **Open** http://localhost:3001
2. **Allow** microphone access
3. **Select** interview mode (Amazon, Google, etc.)
4. **Click** record button and start speaking
5. **Get** real-time AI responses via voice
6. **View** live transcript with conversation history

## 🔧 **API Endpoints**

- `GET /api/health` - System health check
- `GET /api/prompts` - Available interview modes
- `GET /api/transcripts/{session_id}` - Session transcript
- `WebSocket /ws/{session_id}` - Real-time communication

## 🎤 **Voice Providers**

- **Gemini Voice**: Built-in Gemini Live API voice (default)
- **ElevenLabs**: Higher quality synthesis (toggle in UI)

## 🗄️ **Database**

Supabase PostgreSQL with real-time subscriptions:
- `interview_sessions` - Session metadata
- `transcripts` - Conversation history

## 📚 **Documentation**

- **Setup Guide**: `README_SUPABASE.md` - Complete setup instructions
- **Database Schema**: `supabase_schema.sql` - SQL tables and indexes

## 🛠️ **Development**

```bash
# Backend only
npm run supabase-backend

# Frontend only  
npm run frontend

# Production build
npm run build && npm start
```

## 🔑 **Required API Keys**

- **Google AI Studio**: [aistudio.google.com](https://aistudio.google.com/app/apikey)
- **ElevenLabs**: [elevenlabs.io](https://elevenlabs.io/app/settings/api-keys)
- **Supabase**: [supabase.com/dashboard](https://supabase.com/dashboard)

## 📝 **Tech Stack**

- **Backend**: Python + FastAPI + Uvicorn + Supabase
- **Frontend**: Next.js 15 + React 19 + TypeScript + Tailwind + shadcn/ui
- **Database**: PostgreSQL (via Supabase)
- **AI**: Gemini Live API + ElevenLabs API
- **Real-time**: WebSocket + Supabase real-time

---

**Ready for production with a clean, scalable architecture!** 🎉

# Live Audio Chat with Google Gemini

A simple WebSocket-based frontend for bidirectional audio conversations with Google's Gemini Live API.

## Setup

1. Install the dependencies:
```bash
pip install -r requirements.txt
```

2. Set your Google API key as an environment variable:
```bash
export GOOGLE_API_KEY="your_api_key_here"
```

## Usage

1. Start the WebSocket server:
```bash
python websocket_server.py
```

2. Open `frontend.html` in your web browser

3. Click "Start Conversation" to begin talking with Gemini

4. Click "Stop Conversation" to end the session

## Features

- Simple single-button interface
- Real-time bidirectional audio conversation
- WebSocket communication between frontend and backend
- Direct integration with Google Gemini Live API

## Important Notes

- **Use headphones** to prevent audio feedback
- Make sure your browser allows microphone access
- The server runs on `localhost:8765` by default
