# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Frontend (Next.js)
```bash
cd frontend
npm install                     # Install dependencies
npm run dev                     # Start dev server (port 3001)
npm run build                   # Production build
npm run lint                    # Run ESLint
```

### Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt # Install Python dependencies
python simple_supabase_backend.py # Start backend server (port 3000)
```

### Full Stack Development
Always start backend first, then frontend:
```bash
# Terminal 1: Backend
python backend/simple_supabase_backend.py

# Terminal 2: Frontend  
cd frontend && npm run dev
```

## Architecture Overview

This is an AI-powered interview practice application with real-time voice conversations.

**Tech Stack:**
- Frontend: Next.js 15 + React 19 + TypeScript + Tailwind CSS + Shadcn/UI
- Backend: FastAPI + Python + WebSockets
- Database: Supabase (PostgreSQL with RLS)
- Authentication: Clerk
- AI: Google Gemini Live API

**Key Directories:**
- `frontend/src/app/` - Next.js App Router pages
- `frontend/src/components/features/` - Core interview functionality
- `frontend/src/hooks/` - Custom React hooks (esp. `useInterviewSession`)
- `backend/simple_supabase_backend.py` - Main backend server
- `backend/prompts.json` - Interview configurations

## Real-time Voice Flow

```
Frontend (Web Audio API) 
    ↓ WebSocket (16kHz PCM)
Backend (FastAPI) 
    ↓ 
Gemini Live API 
    ↓ (24kHz audio response)
Backend → Frontend (audio playback + transcript)
```

## Database Schema

Key tables:
- `conversations` - Interview sessions
- `transcripts` - Real-time conversation text with speaker identification
- `users` - Clerk authentication integration

## Authentication

Clerk protects routes: `/dashboard`, `/interview`, `/transcripts`
User context flows through WebSocket to backend for transcript association.

## Environment Variables

Frontend requires:
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
- `CLERK_SECRET_KEY`
- `NEXT_PUBLIC_API_URL=http://localhost:3000`
- `NEXT_PUBLIC_WS_URL=ws://localhost:3000`

Backend requires:
- `GOOGLE_API_KEY` (Gemini)
- `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`
- `CLERK_WEBHOOK_SECRET`

## Development Notes

- Backend must run on port 3000, frontend on 3001
- WebSocket connection is critical for real-time audio streaming
- Interview types configured in `backend/prompts.json`
- Transcript capture is automatic during live conversations
- Use `useInterviewSession` hook for interview state management
- All UI components use Shadcn/UI patterns