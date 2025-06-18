# 🚀 How to Run Coimbatore - AI Interview Practice App

## 📋 Environment Files Required

**Total .env files needed: 2**

1. **Root `.env`** (main project directory) - Backend environment variables
2. **Frontend `.env.local`** (frontend directory) - Frontend environment variables

## 🔑 API Keys Required from Project Owner

### **Backend Keys (.env in root directory)**
```bash
# Google Gemini API
GOOGLE_API_KEY=your_google_gemini_api_key_here

# Supabase Database 
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
SUPABASE_ANON_KEY=your_supabase_anon_key

# Clerk Authentication (for webhooks)
CLERK_WEBHOOK_SECRET=your_clerk_webhook_secret
```

### **Frontend Keys (.env.local in frontend/ directory)**
```bash
# Clerk Authentication
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
CLERK_SECRET_KEY=your_clerk_secret_key

# API Endpoints (usually localhost for development)
NEXT_PUBLIC_API_URL=http://localhost:3000
NEXT_PUBLIC_WS_URL=ws://localhost:3000
```

## 🛠️ Step-by-Step Setup Instructions

### **1. Prerequisites**
- **Node.js** (v18 or higher) - [Download here](https://nodejs.org/)
- **Python** (v3.8 or higher) - [Download here](https://python.org/)
- **Git** - [Download here](https://git-scm.com/)

### **2. Clone the Repository**
```bash
git clone https://github.com/your-username/bluegeneration.git
cd bluegeneration
```

### **3. Backend Setup (Python/FastAPI)**

#### **3.1 Navigate to Backend Directory**
```bash
cd backend
```

#### **3.2 Create Virtual Environment**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Verify activation (should show venv path)
which python
```

#### **3.3 Install Python Dependencies**
```bash
# With virtual environment activated
pip install -r requirements.txt
```

#### **3.4 Create Backend Environment File**
Create `.env` file in the **root directory** (not in backend/):
```bash
# Go back to root directory
cd ..

# Create .env file
touch .env
```

Add the backend environment variables provided by the project owner.

#### **3.5 Start Backend Server**
```bash
# From root directory, with venv activated
cd backend
python simple_supabase_backend.py
```

**Backend will run on:** http://localhost:3000

### **4. Frontend Setup (Next.js/React)**

#### **4.1 Open New Terminal and Navigate to Frontend**
```bash
cd frontend
```

#### **4.2 Install Node.js Dependencies**
```bash
npm install
```

#### **4.3 Create Frontend Environment File**
```bash
# In frontend/ directory
touch .env.local
```

Add the frontend environment variables provided by the project owner.

#### **4.4 Start Frontend Development Server**
```bash
npm run dev
```

**Frontend will run on:** http://localhost:3001

## 🎯 Quick Start Commands

**Start both servers (use 2 terminals):**

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # On macOS/Linux
python simple_supabase_backend.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

## 🧪 Testing the Setup

1. **Backend Health Check:** http://localhost:3000/api/health
2. **Frontend:** http://localhost:3001
3. **Sign Up/Login:** Create a Clerk account
4. **Start Interview:** Click "Start Interview" on dashboard

## 🔐 API Keys Source Guide

### **For Project Owner - Where to Get Keys:**

#### **1. Google Gemini API Key**
- Go to [Google AI Studio](https://aistudio.google.com/)
- Sign in with Google account
- Click "Get API Key" → "Create API Key"
- Copy the key for `GOOGLE_API_KEY`

#### **2. Supabase Keys**
- Go to [Supabase Dashboard](https://supabase.com/dashboard)
- Select your project
- Go to Settings → API
- Copy:
  - **URL** → `SUPABASE_URL`
  - **anon public** → `SUPABASE_ANON_KEY`
  - **service_role** → `SUPABASE_SERVICE_ROLE_KEY`

#### **3. Clerk Authentication Keys**
- Go to [Clerk Dashboard](https://dashboard.clerk.com/)
- Select your application
- Go to API Keys
- Copy:
  - **Publishable Key** → `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
  - **Secret Key** → `CLERK_SECRET_KEY`
- Go to Webhooks → Add webhook for user events
- Copy webhook secret → `CLERK_WEBHOOK_SECRET`

## 🚨 Common Issues & Solutions

### **"Module not found" errors**
```bash
# Backend: Activate virtual environment
cd backend && source venv/bin/activate

# Frontend: Reinstall dependencies  
cd frontend && rm -rf node_modules && npm install
```

### **Environment variables not loading**
- Ensure `.env` is in root directory (for backend)
- Ensure `.env.local` is in frontend/ directory
- Restart both servers after adding variables
- Check for typos in variable names

### **Port conflicts**
- Backend: Change port in `simple_supabase_backend.py`
- Frontend: Use `npm run dev -- --port 3002`

### **Database connection issues**
- Verify Supabase project is not paused
- Check Supabase URL format: `https://project-id.supabase.co`
- Ensure service role key has proper permissions

## 📞 Support

If you encounter issues:
1. Check that all environment variables are set correctly
2. Ensure both servers are running
3. Verify API keys have proper permissions
4. Check browser console for frontend errors
5. Check terminal logs for backend errors

## 🎉 Success!

When everything is working:
- ✅ Backend: http://localhost:3000/api/health returns "healthy"
- ✅ Frontend: http://localhost:3001 loads successfully
- ✅ Authentication: Can sign up/login with Clerk
- ✅ Interviews: Can start voice conversations with AI

**Happy coding! 🚀**