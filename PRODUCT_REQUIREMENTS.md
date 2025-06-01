# 🎯 Coimbatore - Product Requirements Document

## 📋 **Product Overview**

### **Vision**
Create the world's most realistic AI-powered interview practice platform that helps candidates prepare for technical interviews at top tech companies through real-time voice conversations with AI interviewers.

### **Mission**
Democratize interview preparation by providing personalized, realistic interview experiences that adapt to each user's skill level and target companies.

---

## 👥 **Target Users**

### **Primary Users**
- **Software Engineers** (Junior to Senior levels)
- **New Graduates** preparing for first tech job
- **Career Switchers** transitioning into tech
- **International Students** needing interview practice in English

### **Secondary Users**
- **Bootcamp Students**
- **Freelancers** seeking full-time positions
- **Engineering Managers** practicing for leadership roles

---

## 🎯 **Core Features**

### **🔐 Authentication & User Management**
- **Clerk Authentication** (Sign up, Login, Social OAuth)
- **User Profiles** (Name, experience level, target companies)
- **Subscription Management** (Free tier, Premium plans)
- **Progress Tracking** (Interview history, performance analytics)

### **🎤 Real-Time Voice Interviews**
- **Live Audio Conversations** with Gemini AI
- **Multiple Interview Types**:
  - Technical Screening
  - Algorithms & Data Structures  
  - System Design
  - Behavioral Questions
  - Company-Specific (Amazon, Google, Microsoft, Meta, Apple)
- **Real-Time Transcription** (User & AI speech)
- **Interruption Handling** (Natural conversation flow)

### **📊 Interview Analytics**
- **Performance Scoring** (Technical accuracy, communication, confidence)
- **Detailed Feedback** (Strengths, areas for improvement)
- **Progress Tracking** (Skill development over time)
- **Interview History** (All past sessions with transcripts)

### **🎯 Personalization**
- **Adaptive Difficulty** (AI adjusts based on performance)
- **Custom Interview Plans** (Based on target company/role)
- **Skill Gap Analysis** (Identify weak areas)
- **Interview Calendar** (Schedule practice sessions)

---

## 🗄️ **Database Schema**

### **Users Table**
```sql
users (
  id: UUID PRIMARY KEY,
  clerk_user_id: VARCHAR UNIQUE NOT NULL,
  email: VARCHAR UNIQUE NOT NULL,
  full_name: VARCHAR,
  experience_level: ENUM('entry', 'junior', 'mid', 'senior', 'staff', 'principal'),
  target_companies: TEXT[], -- ['amazon', 'google', 'microsoft']
  subscription_tier: ENUM('free', 'premium', 'enterprise'),
  created_at: TIMESTAMP DEFAULT NOW(),
  updated_at: TIMESTAMP DEFAULT NOW()
)
```

### **Conversations Table** (Updated)
```sql
conversations (
  id: UUID PRIMARY KEY,
  user_id: UUID REFERENCES users(id) ON DELETE CASCADE,
  session_id: VARCHAR UNIQUE NOT NULL,
  mode: VARCHAR NOT NULL, -- 'amazon_interviewer', 'technical_screening'
  status: ENUM('active', 'completed', 'abandoned'),
  title: VARCHAR,
  duration: INTEGER, -- seconds
  performance_score: DECIMAL(3,2), -- 0.00 to 10.00
  difficulty_level: ENUM('easy', 'medium', 'hard'),
  created_at: TIMESTAMP DEFAULT NOW(),
  completed_at: TIMESTAMP,
  updated_at: TIMESTAMP DEFAULT NOW()
)
```

### **Transcripts Table** (Updated)
```sql
transcripts (
  id: UUID PRIMARY KEY,
  conversation_id: UUID REFERENCES conversations(id) ON DELETE CASCADE,
  user_id: UUID REFERENCES users(id) ON DELETE CASCADE,
  session_id: VARCHAR NOT NULL,
  sequence_number: INTEGER,
  speaker: ENUM('user', 'assistant'),
  text: TEXT NOT NULL,
  provider: VARCHAR, -- 'gemini_speech', 'gemini_text'
  confidence_score: DECIMAL(3,2),
  created_at: TIMESTAMP DEFAULT NOW()
)
```

### **Interview_Feedback Table** (New)
```sql
interview_feedback (
  id: UUID PRIMARY KEY,
  conversation_id: UUID REFERENCES conversations(id) ON DELETE CASCADE,
  user_id: UUID REFERENCES users(id) ON DELETE CASCADE,
  technical_score: DECIMAL(3,2),
  communication_score: DECIMAL(3,2),
  problem_solving_score: DECIMAL(3,2),
  overall_feedback: TEXT,
  strengths: TEXT[],
  improvement_areas: TEXT[],
  recommended_topics: TEXT[],
  created_at: TIMESTAMP DEFAULT NOW()
)
```

---

## 🎨 **User Experience Flow**

### **🏠 Landing Page**
1. **Hero Section** - Value proposition, demo video
2. **Features Overview** - Key benefits with animations
3. **Pricing Tiers** - Free vs Premium comparison
4. **Social Proof** - Testimonials, success stories
5. **CTA Buttons** - "Start Free Trial", "Watch Demo"

### **🔐 Authentication Flow**
1. **Sign Up/Login** - Clerk modal integration
2. **Onboarding** - Experience level, target companies
3. **Dashboard** - Interview history, quick start

### **🎤 Interview Experience**
1. **Interview Selection** - Choose company/type
2. **Pre-Interview Setup** - Microphone test, instructions
3. **Live Interview** - Real-time voice conversation
4. **Post-Interview** - Feedback, score, transcript review
5. **Progress Tracking** - Updated dashboard metrics

---

## 🛠️ **Technical Architecture**

### **Frontend (Next.js 14)**
- **App Router** with TypeScript
- **Tailwind CSS** + **Shadcn/ui** components
- **Clerk** for authentication
- **WebSocket** for real-time audio
- **React Query** for API state management

### **Backend (FastAPI)**
- **Supabase** for database + real-time subscriptions
- **Gemini Live API** for AI conversations
- **WebSocket** for audio streaming
- **Row Level Security** for user data isolation

### **Infrastructure**
- **Vercel** for frontend deployment
- **Railway** for backend deployment  
- **Supabase** for database + auth + storage

---

## 📈 **Success Metrics**

### **User Engagement**
- **Daily Active Users** (DAU)
- **Interview Completion Rate** (>80% target)
- **Session Duration** (15+ minutes average)
- **Return User Rate** (70% weekly retention)

### **Product Performance**
- **Audio Latency** (<200ms)
- **Transcription Accuracy** (>95%)
- **User Satisfaction** (4.5+ stars)

### **Business Metrics**
- **Free to Paid Conversion** (15% target)
- **Monthly Recurring Revenue** (MRR growth)
- **Customer Acquisition Cost** (CAC)

---

## 🎯 **Pricing Strategy**

### **🆓 Free Tier**
- **3 interviews/month**
- **Basic feedback**
- **Standard interview types**
- **Community support**

### **💎 Premium ($19/month)**
- **Unlimited interviews**
- **Detailed analytics**
- **Company-specific interviews**
- **Performance tracking**
- **Priority support**

### **🏢 Enterprise ($99/month)**
- **Team management**
- **Custom interview scenarios**
- **Advanced analytics**
- **API access**
- **Dedicated support**

---

## 🚀 **Development Roadmap**

### **Phase 1: MVP (Week 1-2)**
✅ Basic voice interviews
✅ Real-time transcription
✅ Supabase integration
🔄 **Current**: User authentication + landing page

### **Phase 2: User Platform (Week 3-4)**
- Complete user dashboard
- Interview history & analytics
- Performance scoring system
- Responsive mobile design

### **Phase 3: Advanced Features (Week 5-6)**
- Company-specific interview modes
- Advanced feedback system
- Interview scheduling
- Social features (sharing, leaderboards)

### **Phase 4: Scale & Polish (Week 7-8)**
- Performance optimization
- Advanced analytics
- Mobile app (React Native)
- Enterprise features

---

## 🎯 **Next Steps**

1. ✅ **Landing Page** with modern design
2. ✅ **Clerk Authentication** integration
3. ✅ **Updated Database Schema** with users
4. ✅ **User Dashboard** with interview history
5. ✅ **Backend User Management** APIs

---

*This PRD serves as the foundation for building a world-class interview practice platform that helps candidates land their dream jobs at top tech companies.* 