# 🎯 BlueGeneration - AI Interview Platform

## 📁 Current Codebase Structure

### 🔧 Backend (`/backend`)
**Core Application:**
- `simple_supabase_backend.py` - Main FastAPI WebSocket server with Gemini Live API integration
- `debug_database.py` - Database debugging and diagnostic tools
- `prompts.json` - Interview prompt configurations

**Authentication & User Management:**
- `clerk_user_service.py` - Clerk authentication service integration
- `clerk_webhooks.py` - Webhook handlers for Clerk user events
- `user_api.py` - User management API endpoints

**Database:**
- `supabase_schema_with_users.sql` - Complete database schema with RLS policies

**Documentation:**
- `README_SIMPLE_SUPABASE.md` - Backend setup and API documentation

### 🎨 Frontend (`/frontend`)
**Core Application:**
- `src/app/page.tsx` - Landing page
- `src/app/dashboard/page.tsx` - User dashboard
- `src/app/interview/page.tsx` - Interview session page
- `src/app/layout.tsx` - Root layout with Clerk authentication

**Authentication Pages:**
- `src/app/sign-in/[[...rest]]/page.tsx` - Clerk sign-in page
- `src/app/sign-up/[[...rest]]/page.tsx` - Clerk sign-up page

**Core Components:**
- `src/components/supabase-interview-app.tsx` - Main interview application
- `src/components/features/InterviewSession.tsx` - Interview session management
- `src/components/features/TranscriptManager.tsx` - Transcript handling

**Hooks & Utilities:**
- `src/hooks/useInterviewSession.ts` - WebSocket interview session hook
- `src/hooks/use-toast.ts` - Toast notification hook
- `src/lib/utils.ts` - Utility functions
- `src/types/interview.ts` - TypeScript type definitions

**UI Components:** (Shadcn/UI)
- `src/components/ui/` - Complete UI component library

**Configuration:**
- `middleware.ts` - Clerk authentication middleware
- `next.config.ts` - Next.js configuration
- `tailwind.config.ts` - Tailwind CSS configuration
- `components.json` - Shadcn/UI configuration

### 📚 Documentation
- `README.md` - Main project documentation
- `PRODUCT_REQUIREMENTS.md` - Product requirements and specifications
- `CLERK_SETUP.md` - Clerk authentication setup guide
- `CLERK_SUPABASE_SETUP.md` - Clerk + Supabase integration guide
- `frontend/README.md` - Frontend-specific documentation
- `frontend/SETUP.md` - Frontend setup instructions

### ⚙️ Configuration
- `vercel.json` - Vercel deployment configuration
- `package.json` files - Node.js dependencies and scripts

## 🏗️ Architecture Overview

### Technology Stack
- **Frontend:** Next.js 14, React, TypeScript, Tailwind CSS, Shadcn/UI
- **Backend:** FastAPI, Python, WebSockets
- **Database:** Supabase (PostgreSQL with RLS)
- **Authentication:** Clerk
- **AI:** Google Gemini Live API
- **Deployment:** Vercel (Frontend), Railway/Custom (Backend)

### Key Features
1. **Real-time AI Interviews** - WebSocket-based voice conversations with Gemini
2. **User Authentication** - Clerk-powered sign-up/sign-in with social providers
3. **Interview Management** - Multiple interview types and prompts
4. **Transcript Storage** - Real-time conversation logging to Supabase
5. **User Dashboard** - Interview history and session management

### Current Status
✅ **Completed:**
- Clean codebase with all legacy files removed
- Clerk authentication fully integrated
- Supabase database with proper RLS policies
- WebSocket connection for real-time communication
- Gemini Live API integration
- User ID properly passed from frontend to backend
- Transcript storage with user association

🔧 **Recent Fixes:**
- Removed all Gemini debugging logs while keeping Supabase logs
- Fixed user_id flow from Clerk authentication to conversation creation
- Enhanced error handling and session management
- Cleaned up codebase by removing 20+ irrelevant files

⚠️ **Known Issues:**
- Gemini Live API may start speaking before user clicks "Start Interview"
- Need to verify conversation creation is working with authenticated users

## 🚀 Next Steps
1. Test the complete user flow with authentication
2. Verify conversation and transcript creation
3. Add proper error boundaries and loading states
4. Implement interview feedback and scoring
5. Add deployment configurations for production

## 📝 File Count Summary
- **Backend Python files:** 6
- **Frontend TypeScript/TSX files:** 25
- **Configuration files:** 8
- **Documentation files:** 6
- **Total relevant files:** 45

*Last updated: January 31, 2025* 