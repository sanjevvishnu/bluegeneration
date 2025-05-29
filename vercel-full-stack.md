# 🚀 Full Vercel Deployment - Modern Approach

Since Vercel doesn't support traditional WebSocket servers, we'll create a modern implementation using **Server-Sent Events (SSE)** + **Fetch API** that achieves the same real-time functionality.

## 🏗️ **New Architecture: Full Vercel**

```
Frontend (Vercel) ←→ API Routes (Vercel Edge) ←→ Gemini Live API
    ↓                       ↓
EventSource (SSE)    Edge Functions + KV Storage
```

## 📁 **File Structure for Full Vercel**

```
├── api/
│   ├── audio-upload.ts      # Handle audio uploads
│   ├── audio-stream.ts      # SSE audio responses
│   ├── session-start.ts     # Initialize session
│   └── session-end.ts       # Cleanup session
├── lib/
│   ├── gemini-client.ts     # Gemini Live API client
│   └── session-store.ts     # Session management
└── frontend/ (existing)
```

## 🔧 **Implementation: Vercel API Routes**

### **1. Session Management**
```typescript
// api/session-start.ts
export const config = { runtime: 'edge' }

interface SessionRequest {
  promptId: string
}

export default async function handler(req: Request) {
  if (req.method !== 'POST') {
    return new Response('Method not allowed', { status: 405 })
  }

  const { promptId } = await req.json() as SessionRequest
  const sessionId = generateSessionId()
  
  // Store session in Vercel KV or memory
  await storeSession(sessionId, {
    promptId,
    createdAt: Date.now(),
    status: 'active'
  })
  
  // Initialize Gemini connection for this session
  await initializeGeminiSession(sessionId, promptId)
  
  return Response.json({
    sessionId,
    sseUrl: `/api/audio-stream?sessionId=${sessionId}`
  })
}
```

### **2. Audio Upload Handler**
```typescript
// api/audio-upload.ts
export const config = { runtime: 'edge' }

export default async function handler(req: Request) {
  if (req.method !== 'POST') {
    return new Response('Method not allowed', { status: 405 })
  }

  const formData = await req.formData()
  const sessionId = formData.get('sessionId') as string
  const audioBlob = formData.get('audio') as Blob
  
  if (!sessionId || !audioBlob) {
    return Response.json({ error: 'Missing sessionId or audio' }, { status: 400 })
  }

  try {
    // Convert blob to PCM data
    const audioBuffer = await audioBlob.arrayBuffer()
    
    // Send to Gemini Live API
    const response = await sendAudioToGemini(sessionId, audioBuffer)
    
    // Queue response for SSE stream
    await queueAudioResponse(sessionId, response)
    
    return Response.json({ success: true })
  } catch (error) {
    return Response.json({ error: error.message }, { status: 500 })
  }
}
```

### **3. Server-Sent Events Stream**
```typescript
// api/audio-stream.ts
export const config = { runtime: 'edge' }

export default async function handler(req: Request) {
  const url = new URL(req.url)
  const sessionId = url.searchParams.get('sessionId')
  
  if (!sessionId) {
    return new Response('Missing sessionId', { status: 400 })
  }

  // Create SSE stream
  const { readable, writable } = new TransformStream()
  const writer = writable.getWriter()
  
  // Send SSE headers
  const response = new Response(readable, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'Access-Control-Allow-Origin': '*',
    },
  })

  // Start streaming audio responses
  streamAudioResponses(sessionId, writer)
  
  return response
}

async function streamAudioResponses(sessionId: string, writer: WritableStreamDefaultWriter) {
  try {
    // Send initial connection event
    await writer.write(`data: ${JSON.stringify({ type: 'connected' })}\n\n`)
    
    // Poll for audio responses and stream them
    while (true) {
      const audioData = await getQueuedAudioResponse(sessionId)
      
      if (audioData) {
        await writer.write(`data: ${JSON.stringify({
          type: 'audio',
          data: audioData
        })}\n\n`)
      }
      
      // Check if session is still active
      const session = await getSession(sessionId)
      if (!session || session.status !== 'active') {
        break
      }
      
      // Small delay to prevent excessive polling
      await new Promise(resolve => setTimeout(resolve, 50))
    }
  } catch (error) {
    await writer.write(`data: ${JSON.stringify({
      type: 'error',
      error: error.message
    })}\n\n`)
  } finally {
    await writer.close()
  }
}
```

## 🎯 **Frontend Changes for SSE**

Update the React hook to use SSE instead of WebSocket:

```typescript
// frontend/src/hooks/useInterviewSessionSSE.ts
export function useInterviewSessionSSE({ prompt, onEnd }: UseInterviewSessionProps) {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [eventSource, setEventSource] = useState<EventSource | null>(null)
  
  // Start session with SSE
  const startSession = useCallback(async () => {
    try {
      // Initialize session
      const response = await fetch('/api/session-start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ promptId: prompt?.id })
      })
      
      const { sessionId, sseUrl } = await response.json()
      setSessionId(sessionId)
      
      // Connect to SSE stream
      const es = new EventSource(sseUrl)
      setEventSource(es)
      
      es.onmessage = (event) => {
        const data = JSON.parse(event.data)
        
        if (data.type === 'audio') {
          // Queue audio for playback
          queueAudioChunk(data.data)
        } else if (data.type === 'error') {
          setError(data.error)
        }
      }
      
      es.onerror = () => {
        setError('Connection lost')
      }
      
    } catch (error) {
      setError(`Failed to start session: ${error}`)
    }
  }, [prompt])
  
  // Send audio data
  const sendAudioData = useCallback(async (audioData: ArrayBuffer) => {
    if (!sessionId) return
    
    const formData = new FormData()
    formData.append('sessionId', sessionId)
    formData.append('audio', new Blob([audioData], { type: 'audio/pcm' }))
    
    try {
      await fetch('/api/audio-upload', {
        method: 'POST',
        body: formData
      })
    } catch (error) {
      console.error('Failed to send audio:', error)
    }
  }, [sessionId])
  
  // ... rest of the hook logic
}
```

## 📦 **Session Storage Options**

### **Option 1: Vercel KV (Recommended)**
```typescript
// lib/session-store.ts
import { kv } from '@vercel/kv'

export async function storeSession(sessionId: string, data: any) {
  await kv.set(`session:${sessionId}`, data, { ex: 3600 }) // 1 hour expiry
}

export async function getSession(sessionId: string) {
  return await kv.get(`session:${sessionId}`)
}

export async function queueAudioResponse(sessionId: string, audioData: any) {
  await kv.lpush(`audio:${sessionId}`, audioData)
}

export async function getQueuedAudioResponse(sessionId: string) {
  return await kv.rpop(`audio:${sessionId}`)
}
```

### **Option 2: In-Memory Store (Simple)**
```typescript
// lib/session-store.ts
const sessions = new Map()
const audioQueues = new Map()

export async function storeSession(sessionId: string, data: any) {
  sessions.set(sessionId, data)
  setTimeout(() => sessions.delete(sessionId), 3600000) // 1 hour cleanup
}

export async function getSession(sessionId: string) {
  return sessions.get(sessionId)
}

export async function queueAudioResponse(sessionId: string, audioData: any) {
  if (!audioQueues.has(sessionId)) {
    audioQueues.set(sessionId, [])
  }
  audioQueues.get(sessionId).push(audioData)
}

export async function getQueuedAudioResponse(sessionId: string) {
  const queue = audioQueues.get(sessionId) || []
  return queue.shift()
}
```

## 🔄 **Updated vercel.json**

```json
{
  "name": "ai-interview-practice",
  "version": 2,
  "functions": {
    "api/**/*.ts": {
      "runtime": "edge"
    }
  },
  "env": {
    "GOOGLE_API_KEY": "@google_api_key",
    "KV_URL": "@kv_url",
    "KV_REST_API_URL": "@kv_rest_api_url",
    "KV_REST_API_TOKEN": "@kv_rest_api_token"
  }
}
```

## ⚖️ **Comparison: SSE vs WebSocket**

| Feature | WebSocket (Railway) | SSE (Vercel) |
|---------|-------------------|--------------|
| **Real-time** | Bidirectional ✅ | Unidirectional (+ Fetch) ✅ |
| **Latency** | Lower ✅ | Slightly higher |
| **Browser Support** | Universal ✅ | Universal ✅ |
| **Deployment** | Separate service | Single platform ✅ |
| **Scaling** | Manual | Automatic ✅ |
| **Cost** | Two platforms | One platform ✅ |
| **Complexity** | Lower ✅ | Moderate |

## 🎯 **Recommendation**

### **For Production (Current)**: 
**Stick with Railway + Vercel** 
- ✅ Native WebSocket support
- ✅ Lower latency
- ✅ Simpler implementation
- ✅ Proven architecture

### **For Single Platform**: 
**Implement Full Vercel with SSE**
- ✅ Single deployment platform
- ✅ Auto-scaling
- ✅ Unified billing
- ⚠️ More complex implementation
- ⚠️ Slightly higher latency

## 🚀 **Would you like me to implement the Full Vercel approach?**

I can create:
1. **Complete API routes** for SSE-based audio streaming
2. **Updated React hooks** for EventSource + Fetch
3. **Session management** with Vercel KV
4. **Deployment configuration** for single-platform deployment

The current Railway approach is production-ready and simpler, but the Full Vercel approach would give you single-platform deployment with automatic scaling! 