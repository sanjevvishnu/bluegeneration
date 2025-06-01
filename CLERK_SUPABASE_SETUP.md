# 🔗 Clerk + Supabase Integration Setup Guide

## 📋 **Complete Setup Instructions**

### **Step 1: Database Schema Setup**

Since Supabase doesn't allow executing SQL via REST API, you need to run the schema manually:

1. **Open Supabase Dashboard**
   - Go to [supabase.com/dashboard](https://supabase.com/dashboard)
   - Select your project
   - Navigate to **SQL Editor** in the left sidebar

2. **Run the Schema**
   - Copy the entire contents of `backend/supabase_schema_with_users.sql`
   - Paste it into the SQL Editor
   - Click **Run** to execute the schema

3. **Verify Tables Created**
   - Go to **Table Editor** in the sidebar
   - You should see these new tables:
     - `users` (with Clerk integration)
     - `conversations` (updated with user_id)
     - `transcripts` (updated with user_id)
     - `interview_feedback` (new)

### **Step 2: Environment Variables**

Update your `backend/.env` file:

```env
# Existing variables
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
GOOGLE_API_KEY=your_google_api_key

# New Clerk variables
CLERK_WEBHOOK_SECRET=whsec_your_webhook_secret_here
```

Update your `frontend/.env.local` file:

```env
# Clerk Authentication
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
CLERK_SECRET_KEY=sk_test_your_secret_key_here
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/dashboard
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/dashboard

# Backend API
NEXT_PUBLIC_API_URL=http://localhost:3000
NEXT_PUBLIC_WS_URL=ws://localhost:3000
```

### **Step 3: Clerk Dashboard Configuration**

1. **Create Clerk Application**
   - Go to [clerk.com](https://clerk.com) and sign up
   - Create a new application
   - Choose "Next.js" as your framework

2. **Configure Redirect URLs**
   - In Clerk Dashboard → **Paths**:
     - Sign-in redirect: `http://localhost:3001/dashboard`
     - Sign-up redirect: `http://localhost:3001/dashboard`
     - Sign-out redirect: `http://localhost:3001/`

3. **Set Up Webhooks**
   - Go to **Webhooks** in Clerk Dashboard
   - Click **Add Endpoint**
   - URL: `http://localhost:3000/webhooks/clerk`
   - Events to listen for:
     - `user.created`
     - `user.updated`
     - `user.deleted`
   - Copy the webhook secret to your `.env` file

4. **Configure Allowed Origins**
   - In **Settings** → **Allowed Origins**:
     - Add `http://localhost:3001`
     - Add `http://localhost:3000`

### **Step 4: Test the Integration**

1. **Start the Backend**
   ```bash
   cd backend
   python simple_supabase_backend.py
   ```
   
   You should see:
   ```
   ✅ Clerk integration modules loaded
   ✅ Clerk authentication routers added
   ```

2. **Start the Frontend**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Test Authentication Flow**
   - Visit `http://localhost:3001`
   - Click "Start Free Trial" or "Sign In"
   - Complete the authentication process
   - Should redirect to `/dashboard`
   - Check Supabase → Table Editor → `users` table for new user record

## 🚀 **What's Now Available**

### **New API Endpoints**

#### **User Management**
- `GET /api/user/profile` - Get user profile
- `PUT /api/user/profile` - Update user profile
- `GET /api/user/stats` - Get user statistics
- `GET /api/user/conversations` - Get user's conversations
- `POST /api/user/check-interview-limit` - Check if user can start interview
- `POST /api/user/start-interview` - Start new interview (increments usage)

#### **Webhooks**
- `POST /webhooks/clerk` - Clerk user lifecycle webhooks
- `GET /webhooks/health` - Webhook health check

### **Authentication-Aware Frontend**
- **Landing Page**: Dynamic navigation based on auth status
- **Dashboard**: Personalized with real user data
- **Interview Page**: Protected route
- **User Stats**: Real interview statistics from database

### **Subscription Management**
- **Free Tier**: 3 interviews per month
- **Premium**: Unlimited interviews
- **Enterprise**: Unlimited + advanced features

## 🧪 **Testing the Integration**

### **Manual User Creation (for testing)**

If webhooks aren't working, you can manually create users:

```bash
curl -X POST http://localhost:3000/api/user/create-user \
  -H "Content-Type: application/json" \
  -d '{
    "id": "user_test123",
    "email_addresses": [{"email_address": "test@example.com", "primary": true}],
    "first_name": "Test",
    "last_name": "User"
  }'
```

### **Test User Stats**

```bash
curl -H "Authorization: Bearer user_test123" \
     http://localhost:3000/api/user/stats
```

### **Test Interview Limits**

```bash
curl -X POST -H "Authorization: Bearer user_test123" \
     http://localhost:3000/api/user/check-interview-limit
```

## 🔧 **Database Schema Overview**

### **Users Table**
```sql
- id (UUID, primary key)
- clerk_user_id (unique, indexed)
- email (unique)
- full_name
- experience_level (enum)
- target_companies (array)
- subscription_tier (enum)
- interviews_used_this_month (integer)
- created_at, updated_at
```

### **Updated Conversations Table**
```sql
- id (UUID, primary key)
- user_id (foreign key to users)
- session_id (unique)
- mode, status, title
- duration, performance_score
- difficulty_level (enum)
- created_at, completed_at, updated_at
```

### **Updated Transcripts Table**
```sql
- id (UUID, primary key)  
- conversation_id (foreign key)
- user_id (foreign key to users)
- session_id
- sequence_number, speaker, text
- provider, confidence_score
- created_at
```

### **Row Level Security (RLS)**
- Users can only access their own data
- Automatic filtering based on Clerk user ID
- Secure multi-tenant architecture

## 🔄 **User Flow**

1. **User signs up** → Clerk webhook creates user in Supabase
2. **User accesses dashboard** → Shows personalized stats and interview history
3. **User starts interview** → Checks subscription limits, increments usage
4. **Interview completion** → Saves transcript and feedback with user association
5. **User views history** → Only sees their own interviews and data

## 🚧 **Production Considerations**

### **Security**
- Enable JWT validation in production (currently simplified for development)
- Use proper Clerk JWT verification in `get_clerk_user_id()`
- Set up proper CORS origins
- Use HTTPS for webhook endpoints

### **Scalability**
- Add database connection pooling
- Implement caching for user data
- Add rate limiting for API endpoints
- Monitor webhook delivery and add retry logic

### **Monitoring**
- Add logging for all user actions
- Monitor subscription usage and limits
- Track authentication errors
- Set up alerts for failed webhooks

---

*Once setup is complete, your Coimbatore platform will have full user authentication, personalized dashboards, subscription management, and secure data isolation!* 