# 🚀 Deployment Guide

This guide will help you deploy the AI Interview Practice App to production using Vercel for the frontend and Railway (or similar) for the backend WebSocket server.

## 🏗️ **Architecture Overview**

```
Frontend (Vercel)     ←→     Backend (Railway/Render)
    ↓                            ↓
Next.js App                Python WebSocket Server
React Components           Gemini Live API Integration
```

## 📦 **Step 1: Deploy Backend (WebSocket Server)**

### Option A: Railway (Recommended)

1. **Create Railway Account**: Go to [railway.app](https://railway.app)

2. **Connect Repository**: 
   - Click "Deploy from GitHub repo"
   - Select your `bluegeneration` repository

3. **Configure Service**:
   - Railway will auto-detect Python
   - Set the following environment variables in Railway:
     ```
     GOOGLE_API_KEY=your_gemini_api_key_here
     PORT=8765
     ```

4. **Create `railway.json`**: Add this file to your root directory:
   ```json
   {
     "$schema": "https://railway.app/railway.schema.json",
     "build": {
       "builder": "NIXPACKS"
     },
     "deploy": {
       "startCommand": "python websocket_server.py",
       "healthcheckPath": "/health",
       "healthcheckTimeout": 100,
       "restartPolicyType": "ON_FAILURE",
       "restartPolicyMaxRetries": 10
     }
   }
   ```

5. **Deploy**: Railway will automatically deploy your WebSocket server

### Option B: Render

1. **Create Render Account**: Go to [render.com](https://render.com)

2. **Create Web Service**:
   - Connect your GitHub repository
   - Choose "Web Service"
   - Runtime: Python 3

3. **Configure**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python websocket_server.py`
   - Environment Variables:
     ```
     GOOGLE_API_KEY=your_gemini_api_key_here
     PORT=8765
     ```

## 📱 **Step 2: Deploy Frontend to Vercel**

### 1. **Install Vercel CLI**
```bash
npm install -g vercel
```

### 2. **Login to Vercel**
```bash
vercel login
```

### 3. **Configure Environment Variables**

In your Vercel dashboard or via CLI, set:
```bash
# Replace with your actual backend URL
NEXT_PUBLIC_WS_URL=wss://your-backend-railway-url.railway.app

# Example URLs:
# Railway: wss://bluegeneration-production.up.railway.app
# Render: wss://bluegeneration.onrender.com
```

### 4. **Deploy Frontend**
```bash
# From project root
vercel --prod

# Or configure via vercel.json (already created)
vercel deploy --prod
```

## 🔧 **Step 3: Update WebSocket URL**

### **Get Backend URL**

**Railway**:
- Go to your Railway dashboard
- Copy the public domain (e.g., `bluegeneration-production.up.railway.app`)
- WebSocket URL: `wss://bluegeneration-production.up.railway.app`

**Render**:
- Go to your Render dashboard  
- Copy the service URL (e.g., `bluegeneration.onrender.com`)
- WebSocket URL: `wss://bluegeneration.onrender.com`

### **Set in Vercel**

1. Go to Vercel Dashboard → Project → Settings → Environment Variables
2. Add: `NEXT_PUBLIC_WS_URL` = `wss://your-backend-url.com`
3. Redeploy: `vercel --prod`

## ⚙️ **Step 4: Backend Configuration for Production**

Update `websocket_server.py` for production:

```python
import os
import websockets
from websockets.server import serve

# Add at the top
PORT = int(os.environ.get('PORT', 8765))
HOST = '0.0.0.0'  # Allow external connections

# Update the main function
async def main():
    print(f"🚀 Starting WebSocket server on {HOST}:{PORT}")
    
    # Add CORS headers for production
    async def handler(websocket, path):
        try:
            await handle_client(websocket, path)
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Client disconnected")
        except Exception as e:
            print(f"❌ Handler error: {e}")

    # Start server with proper configuration
    server = await serve(
        handler, 
        HOST, 
        PORT,
        # Add these for production
        ping_interval=20,
        ping_timeout=10,
        close_timeout=10
    )
    
    print(f"✅ WebSocket server running on ws://{HOST}:{PORT}")
    await server.wait_closed()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## 🌐 **Step 5: Test Deployment**

1. **Frontend**: Visit your Vercel URL (e.g., `https://bluegeneration.vercel.app`)
2. **Backend**: Check Railway/Render logs for successful startup
3. **Connection**: Test WebSocket connection by starting an interview

## 🔑 **Required Environment Variables**

### **Backend (Railway/Render)**
```
GOOGLE_API_KEY=your_gemini_api_key_here
PORT=8765
```

### **Frontend (Vercel)**
```
NEXT_PUBLIC_WS_URL=wss://your-backend-url.com
```

## 🛠️ **Troubleshooting**

### **WebSocket Connection Issues**

1. **CORS Errors**: Ensure backend allows cross-origin requests
2. **SSL/TLS**: Use `wss://` (not `ws://`) for production
3. **Port Issues**: Backend services often assign random ports - use environment PORT

### **Audio Issues**

1. **HTTPS Required**: Modern browsers require HTTPS for microphone access
2. **WebRTC**: Ensure proper audio permissions in production

### **Backend Logs**

**Railway**: 
```bash
railway logs
```

**Render**: 
Check logs in Render dashboard

## 📈 **Scaling Considerations**

1. **Railway**: Automatically scales, pay-per-use
2. **Render**: Multiple instance support for high traffic
3. **WebSocket Limits**: Consider connection pooling for heavy usage
4. **API Quotas**: Monitor Gemini API usage and rate limits

## 🔄 **Continuous Deployment**

Both Railway and Render support automatic deploys:
- **Push to main branch** → Automatic deployment
- **Environment variables** → Managed in platform dashboards
- **Build logs** → Available in real-time

## 💡 **Pro Tips**

1. **Use Railway for backend** - Better WebSocket support
2. **Monitor logs** during first deployment
3. **Test locally first** with production environment variables
4. **Use HTTPS** everywhere in production
5. **Set up health checks** for backend monitoring

---

**🎉 Your AI Interview Practice App is now live!**

Frontend: `https://your-app.vercel.app`  
Backend: `wss://your-backend.railway.app` 