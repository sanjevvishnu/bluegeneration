'use client'

import { useState, useRef } from 'react'
import { Button } from '@/components/ui/button'

export function WebSocketTest() {
  const [status, setStatus] = useState<string>('Disconnected')
  const [messages, setMessages] = useState<string[]>([])
  const wsRef = useRef<WebSocket | null>(null)

  const connect = () => {
    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:3000'}/ws/test-${Date.now()}`
    console.log('🔗 Connecting to:', wsUrl)
    console.log('🔗 Environment variables:', {
      NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL,
      NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL
    })
    
    setStatus('Connecting...')
    setMessages([])
    
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws
    
    ws.onopen = () => {
      console.log('✅ WebSocket connected')
      setStatus('Connected')
      setMessages(prev => [...prev, '✅ Connected to WebSocket'])
      
      // Send a test message
      ws.send(JSON.stringify({
        type: 'create_session',
        data: {
          mode: 'amazon_interviewer',
          session_id: `test-${Date.now()}`
        }
      }))
    }
    
    ws.onmessage = (event) => {
      console.log('📨 Received:', event.data)
      setMessages(prev => [...prev, `📨 Received: ${event.data}`])
    }
    
    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error)
      setStatus('Error')
      setMessages(prev => [...prev, `❌ Error: ${JSON.stringify(error)}`])
    }
    
    ws.onclose = (event) => {
      console.log('🔌 WebSocket closed:', event.code, event.reason)
      setStatus('Disconnected')
      setMessages(prev => [...prev, `🔌 Closed: ${event.code} - ${event.reason}`])
    }
  }
  
  const disconnect = () => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }
  
  return (
    <div className="p-4 border rounded-lg space-y-4">
      <h3 className="text-lg font-semibold">WebSocket Test</h3>
      <div className="flex items-center space-x-2">
        <span>Status: </span>
        <span className={`font-medium ${
          status === 'Connected' ? 'text-green-600' : 
          status === 'Error' ? 'text-red-600' : 
          'text-gray-600'
        }`}>
          {status}
        </span>
      </div>
      <div className="flex space-x-2">
        <Button onClick={connect} disabled={status === 'Connected'}>
          Connect
        </Button>
        <Button onClick={disconnect} disabled={status === 'Disconnected'}>
          Disconnect
        </Button>
      </div>
      <div className="space-y-1 max-h-40 overflow-y-auto">
        <h4 className="font-medium">Messages:</h4>
        {messages.map((msg, i) => (
          <div key={i} className="text-sm font-mono bg-gray-100 p-2 rounded">
            {msg}
          </div>
        ))}
      </div>
    </div>
  )
} 