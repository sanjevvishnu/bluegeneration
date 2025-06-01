# 🔐 Clerk Authentication Setup Guide

## 📋 **Quick Setup Instructions**

### **1. Create Clerk Account**
1. Go to [clerk.com](https://clerk.com) and sign up
2. Create a new application
3. Choose "Next.js" as your framework

### **2. Get API Keys**
From your Clerk dashboard, copy:
- **Publishable Key** (starts with `pk_`)
- **Secret Key** (starts with `sk_`)

### **3. Environment Variables**
Create `frontend/.env.local` with:

```env
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

### **4. Clerk Dashboard Configuration**

#### **Redirect URLs:**
- **Sign-in redirect**: `http://localhost:3001/dashboard`
- **Sign-up redirect**: `http://localhost:3001/dashboard`
- **Sign-out redirect**: `http://localhost:3001/`

#### **Allowed Origins:**
- `http://localhost:3001`
- `http://localhost:3000` (for API calls)

### **5. Test Authentication**
1. Start the frontend: `npm run dev`
2. Visit `http://localhost:3001`
3. Click "Sign In" or "Start Free Trial"
4. Complete authentication flow
5. Should redirect to `/dashboard`

## 🚀 **What's Already Configured**

### **✅ Frontend Integration**
- **Landing Page**: Authentication-aware navigation
- **Dashboard**: Protected route with user information
- **Interview Page**: Protected route
- **Middleware**: Route protection for `/dashboard/*`, `/interview/*`

### **✅ UI Components**
- **SignInButton/SignUpButton**: Modal authentication
- **UserButton**: Profile management dropdown
- **Protected Routes**: Automatic redirect to sign-in

### **✅ User Experience**
- **Conditional Navigation**: Different buttons for authenticated/unauthenticated users
- **Personalized Dashboard**: Welcome message with user's first name
- **Seamless Flow**: Landing page → Authentication → Dashboard → Interview

## 🔄 **Next Steps**

### **1. Update Backend for Users**
- Modify backend to create user records from Clerk webhooks
- Add user_id to conversations and transcripts
- Implement user-specific data filtering

### **2. Supabase Integration**
- Run the new database schema with users table
- Set up Row Level Security policies
- Connect Clerk user IDs to Supabase users

### **3. Enhanced Features**
- User onboarding flow
- Subscription management
- Interview history and analytics
- Profile customization

## 🔧 **Troubleshooting**

### **Common Issues:**
1. **"Invalid publishable key"**: Check environment variable names
2. **Redirect loops**: Verify redirect URLs in Clerk dashboard
3. **CORS errors**: Add localhost origins to Clerk settings
4. **Middleware issues**: Ensure middleware.ts is in root directory

### **Development Tips:**
- Use Clerk's development instance for testing
- Check browser console for authentication errors
- Verify environment variables are loaded correctly
- Test both sign-in and sign-up flows

## 📚 **Resources**
- [Clerk Next.js Documentation](https://clerk.com/docs/nextjs)
- [Clerk Dashboard](https://dashboard.clerk.com/)
- [Authentication Components](https://clerk.com/docs/components)

---

*Once you've completed the Clerk setup, users can authenticate and access the full platform with personalized dashboards and interview tracking!* 