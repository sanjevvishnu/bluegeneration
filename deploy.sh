#!/bin/bash

# 🚀 Deployment Script for AI Interview Practice App

echo "🎯 AI Interview Practice App - Deployment Script"
echo "================================================"

# Check if required tools are installed
command -v vercel >/dev/null 2>&1 || { 
    echo "❌ Vercel CLI not found. Install with: npm install -g vercel"
    exit 1
}

# Check if git is clean
if [[ `git status --porcelain` ]]; then
    echo "⚠️  You have uncommitted changes. Please commit first:"
    git status --short
    exit 1
fi

echo "✅ Git working directory is clean"

# Ask for backend URL
echo ""
echo "🔧 Configuration Required:"
read -p "Enter your backend WebSocket URL (e.g., wss://your-app.railway.app): " BACKEND_URL

if [[ -z "$BACKEND_URL" ]]; then
    echo "❌ Backend URL is required"
    exit 1
fi

# Validate URL format
if [[ ! "$BACKEND_URL" =~ ^wss:// ]]; then
    echo "⚠️  Warning: Backend URL should start with 'wss://' for production"
fi

echo ""
echo "🔧 Setting environment variables in Vercel..."

# Set environment variable in Vercel
vercel env add NEXT_PUBLIC_WS_URL production <<< "$BACKEND_URL"

echo "✅ Environment variable set"

echo ""
echo "🚀 Deploying frontend to Vercel..."

# Deploy to Vercel
vercel --prod

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Deployment successful!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Ensure your backend is deployed and running"
    echo "2. Test the WebSocket connection"
    echo "3. Try starting an interview session"
    echo ""
    echo "🔧 Backend deployment:"
    echo "- Railway: https://railway.app"
    echo "- Render: https://render.com" 
    echo "- See DEPLOYMENT.md for detailed instructions"
else
    echo "❌ Deployment failed"
    exit 1
fi 