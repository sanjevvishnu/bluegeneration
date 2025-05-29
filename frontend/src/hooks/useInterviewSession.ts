'use client'

import { useState, useRef, useCallback, useEffect } from 'react'

// Define types inline to avoid import issues
interface InterviewPrompt {
  id: string
  name: string
  systemInstruction: string
}

interface TranscriptEntry {
  id: string
  speaker: 'user' | 'ai'
  content: string
  timestamp: Date
}

interface InterviewSession {
  id: string
  promptId: string
  startTime: Date
  endTime?: Date
  status: 'connecting' | 'active' | 'completed'
  transcript: TranscriptEntry[]
}

// Generate session ID utility
const generateSessionId = () => {
  return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15)
}

interface WebSocketMessage {
  type: string
  data?: any
}

interface UseInterviewSessionProps {
  prompt: InterviewPrompt | null
  onEnd: () => void
}

interface UseInterviewSessionReturn {
  session: InterviewSession | null
  transcript: TranscriptEntry[]
  isConnected: boolean
  isRecording: boolean
  volumeLevel: number
  error: string | null
  startSession: () => Promise<void>
  endSession: () => void
  startRecording: () => Promise<void>
  stopRecording: () => void
  sendTextMessage: (message: string) => void
}

// Audio queue management for proper interruption handling
interface AudioQueueItem {
  data: ArrayBuffer
  timestamp: number
  id: string
}

export function useInterviewSession({ 
  prompt, 
  onEnd 
}: UseInterviewSessionProps): UseInterviewSessionReturn {
  // Session state
  const [session, setSession] = useState<InterviewSession | null>(null)
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [volumeLevel, setVolumeLevel] = useState(0)
  const [error, setError] = useState<string | null>(null)

  // Refs for WebSocket and audio
  const wsRef = useRef<WebSocket | null>(null)
  const sessionIdRef = useRef<string>(generateSessionId())
  const audioStreamRef = useRef<MediaStream | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const volumeIntervalRef = useRef<NodeJS.Timeout | null>(null)

  // Audio refs
  const processorRef = useRef<ScriptProcessorNode | null>(null)
  
  // Audio queue management for interruption support
  const audioQueueRef = useRef<AudioQueueItem[]>([])
  const isPlayingAudioRef = useRef(false)
  const currentAudioSourceRef = useRef<AudioBufferSourceNode | null>(null)

  // Cleanup function
  const cleanup = useCallback(() => {
    console.log('🧹 Cleaning up session...')
    
    // Stop audio recording
    if (audioStreamRef.current) {
      audioStreamRef.current.getTracks().forEach(track => track.stop())
      audioStreamRef.current = null
    }
    
    // Cleanup audio processing
    if (processorRef.current) {
      processorRef.current.disconnect()
      processorRef.current = null
    }
    
    // Clear audio queue and stop current playback
    audioQueueRef.current = []
    if (currentAudioSourceRef.current) {
      try {
        currentAudioSourceRef.current.stop()
      } catch (e) {
        // Source might already be stopped
      }
      currentAudioSourceRef.current = null
    }
    isPlayingAudioRef.current = false
    
    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    
    // Reset state
    setIsConnected(false)
    setIsRecording(false)
    setError(null)
    
    console.log('✅ Session cleanup completed')
  }, [])

  // Start session
  const startSession = useCallback(async () => {
    if (isConnected) return

    try {
      setError(null)
      console.log('🚀 Starting interview session...')

      // Create WebSocket connection to websocket_server.py
      const ws = new WebSocket('ws://localhost:8765')
      wsRef.current = ws

      ws.onopen = () => {
        console.log('✅ Connected to WebSocket server')
        
        // Send prompt selection if available
        if (prompt) {
          ws.send(JSON.stringify({
            type: 'prompt_selection',
            prompt: prompt.id
          }))
          console.log(`📝 Sent prompt selection: ${prompt.id}`)
        }
        
        setIsConnected(true)
      }

      ws.onmessage = (event) => {
        try {
          if (typeof event.data === 'string') {
            // Text message (JSON)
            const data = JSON.parse(event.data)
            console.log('📨 Received message:', data.type)
            
            if (data.type === 'error') {
              setError(data.data?.message || 'Unknown error')
            } else if (data.type === 'prompt_configured') {
              console.log('✅ Prompt configured successfully')
              setSession((prev: InterviewSession | null) => prev ? { ...prev, status: 'active' } : null)
            }
          } else if (event.data instanceof Blob) {
            // Binary audio data from Gemini Live API
            console.log('🔊 Received audio blob:', event.data.size, 'bytes')
            event.data.arrayBuffer().then(queueAudioChunk)
          } else if (event.data instanceof ArrayBuffer) {
            // Direct binary audio data
            console.log('🔊 Received audio buffer:', event.data.byteLength, 'bytes')
            queueAudioChunk(event.data)
          }
        } catch (err) {
          console.error('❌ Error processing WebSocket message:', err)
        }
      }

      ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error)
        setError('WebSocket connection error')
      }

      ws.onclose = (event) => {
        console.log('🔌 WebSocket connection closed:', event.code, event.reason)
        setIsConnected(false)
        if (event.code !== 1000) { // Not normal closure
          setError('Connection lost')
        }
      }

    } catch (err) {
      console.error('❌ Error starting session:', err)
      setError(`Failed to start session: ${err}`)
    }
  }, [isConnected, prompt])

  // Queue audio chunk for sequential playback with interruption support
  const queueAudioChunk = useCallback(async (arrayBuffer: ArrayBuffer) => {
    try {
      console.log(`🎵 Queueing audio chunk: ${arrayBuffer.byteLength} bytes`)
      
      const audioItem: AudioQueueItem = {
        data: arrayBuffer,
        timestamp: Date.now(),
        id: Math.random().toString(36).substr(2, 9)
      }
      
      audioQueueRef.current.push(audioItem)
      console.log(`📥 Audio queue length: ${audioQueueRef.current.length}`)
      
      // Start processing queue if not already playing
      if (!isPlayingAudioRef.current) {
        processAudioQueue()
      }
    } catch (error) {
      console.error('❌ Error queueing audio chunk:', error)
    }
  }, [])

  // Process audio queue sequentially
  const processAudioQueue = useCallback(async () => {
    if (isPlayingAudioRef.current || audioQueueRef.current.length === 0) {
      return
    }

    console.log('🎶 Starting audio queue processing...')
    isPlayingAudioRef.current = true

    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)()
    }

    // Resume audio context if suspended
    if (audioContextRef.current.state === 'suspended') {
      await audioContextRef.current.resume()
      console.log('🔊 Audio context resumed for queue processing')
    }

    try {
      while (audioQueueRef.current.length > 0) {
        const audioItem = audioQueueRef.current.shift()
        if (!audioItem) break

        console.log(`🎵 Playing audio chunk ${audioItem.id}: ${audioItem.data.byteLength} bytes`)
        
        // Play audio chunk and wait for it to complete
        await playAudioChunkSequentially(audioItem.data)
        
        console.log(`✅ Completed audio chunk ${audioItem.id}`)
        
        // Small delay between chunks to prevent audio artifacts
        await new Promise(resolve => setTimeout(resolve, 50))
      }
    } catch (error) {
      console.error('❌ Error processing audio queue:', error)
    } finally {
      console.log('🎶 Audio queue processing completed')
      isPlayingAudioRef.current = false
    }
  }, [])

  // Play audio chunk sequentially (wait for completion)
  const playAudioChunkSequentially = useCallback(async (arrayBuffer: ArrayBuffer): Promise<void> => {
    return new Promise((resolve, reject) => {
      try {
        if (!audioContextRef.current) {
          throw new Error('Audio context not available')
        }

        // Handle raw PCM data from Gemini Live API (24kHz, 16-bit, mono)
        const sampleRate = 24000
        const channels = 1
        const bytesPerSample = 2
        const numSamples = arrayBuffer.byteLength / bytesPerSample
        
        if (numSamples === 0) {
          console.warn('⚠️ Empty audio buffer received')
          resolve()
          return
        }

        const audioBuffer = audioContextRef.current.createBuffer(channels, numSamples, sampleRate)
        const channelData = audioBuffer.getChannelData(0)
        
        const int16Array = new Int16Array(arrayBuffer)
        for (let i = 0; i < numSamples; i++) {
          channelData[i] = int16Array[i] / 32768.0
        }
        
        const source = audioContextRef.current.createBufferSource()
        source.buffer = audioBuffer
        source.connect(audioContextRef.current.destination)
        
        // Store reference to current source for interruption
        currentAudioSourceRef.current = source
        
        // Set up completion handler
        source.onended = () => {
          console.log(`🔊 Audio chunk completed: ${numSamples} samples`)
          currentAudioSourceRef.current = null
          resolve()
        }
        
        // Start playback immediately (not scheduled)
        source.start()
        
        console.log(`🔊 Started playing audio: ${numSamples} samples at ${sampleRate}Hz`)
        
      } catch (error) {
        console.error('❌ Error playing sequential audio chunk:', error)
        reject(error)
      }
    })
  }, [])

  // Clear audio queue and stop current playback (for interruptions)
  const clearAudioQueue = useCallback(() => {
    console.log('⚡ Clearing audio queue due to interruption - stopping all AI audio')
    
    // Clear the queue
    const queueLength = audioQueueRef.current.length
    audioQueueRef.current = []
    
    // Stop current audio playback immediately
    if (currentAudioSourceRef.current) {
      try {
        currentAudioSourceRef.current.stop()
        console.log('🛑 Stopped current audio source')
      } catch (e) {
        // Source might already be stopped
        console.log('⚠️ Audio source was already stopped')
      }
      currentAudioSourceRef.current = null
    }
    
    // Reset playback state
    isPlayingAudioRef.current = false
    
    console.log(`✅ Audio queue cleared: removed ${queueLength} pending audio chunks`)
  }, [])

  // Play raw PCM audio directly
  const playRawPCMAudio = useCallback(async (arrayBuffer: ArrayBuffer) => {
    try {
      console.log('🔊 playRawPCMAudio called with', arrayBuffer.byteLength, 'bytes')
      
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)()
        console.log('🎧 Created new AudioContext')
      }

      // Resume audio context if it's suspended (required by browsers)
      if (audioContextRef.current.state === 'suspended') {
        await audioContextRef.current.resume()
        console.log('🔊 Audio context resumed, state:', audioContextRef.current.state)
      }

      // Handle raw PCM data from Gemini Live API (24kHz, 16-bit, mono)
      const sampleRate = 24000
      const channels = 1
      const bytesPerSample = 2
      const numSamples = arrayBuffer.byteLength / bytesPerSample
      
      console.log(`🎵 Audio specs: ${numSamples} samples, ${sampleRate}Hz, ${channels} channel(s)`)

      if (numSamples > 0) {
        const audioBuffer = audioContextRef.current.createBuffer(channels, numSamples, sampleRate)
        const channelData = audioBuffer.getChannelData(0)
        
        const int16Array = new Int16Array(arrayBuffer)
        for (let i = 0; i < numSamples; i++) {
          channelData[i] = int16Array[i] / 32768.0
        }
        
        const source = audioContextRef.current.createBufferSource()
        source.buffer = audioBuffer
        source.connect(audioContextRef.current.destination)
        source.start()
        
        console.log(`🔊 Playing audio: ${numSamples} samples at ${sampleRate}Hz`)
      } else {
        console.warn('⚠️ Empty audio buffer received')
      }
    } catch (error) {
      console.error('❌ Error playing raw PCM audio:', error)
    }
  }, [])

  // Play test audio to verify Web Audio API
  const playTestAudio = useCallback(async () => {
    try {
      console.log('🧪 Playing test audio (440Hz tone)...')
      
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)()
      }

      if (audioContextRef.current.state === 'suspended') {
        await audioContextRef.current.resume()
      }

      // Create a 1-second 440Hz tone
      const sampleRate = audioContextRef.current.sampleRate
      const duration = 1.0
      const numSamples = Math.floor(sampleRate * duration)
      
      const audioBuffer = audioContextRef.current.createBuffer(1, numSamples, sampleRate)
      const channelData = audioBuffer.getChannelData(0)
      
      for (let i = 0; i < numSamples; i++) {
        channelData[i] = Math.sin(2 * Math.PI * 440 * i / sampleRate) * 0.3
      }
      
      const source = audioContextRef.current.createBufferSource()
      source.buffer = audioBuffer
      source.connect(audioContextRef.current.destination)
      source.start()
      
      console.log('✅ Test audio played successfully')
    } catch (error) {
      console.error('❌ Error playing test audio:', error)
    }
  }, [])

  // Play audio chunk
  const playAudioChunk = useCallback(async (audioBase64: string) => {
    try {
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)()
      }

      // Resume audio context if it's suspended (required by browsers)
      if (audioContextRef.current.state === 'suspended') {
        await audioContextRef.current.resume()
        console.log('🔊 Audio context resumed')
      }

      const audioData = atob(audioBase64)
      const arrayBuffer = new ArrayBuffer(audioData.length)
      const view = new Uint8Array(arrayBuffer)
      
      for (let i = 0; i < audioData.length; i++) {
        view[i] = audioData.charCodeAt(i)
      }

      // Handle raw PCM data from Gemini Live API (24kHz, 16-bit, mono)
      const sampleRate = 24000
      const channels = 1
      const bytesPerSample = 2
      const numSamples = arrayBuffer.byteLength / bytesPerSample
      
      if (numSamples > 0) {
        const audioBuffer = audioContextRef.current.createBuffer(channels, numSamples, sampleRate)
        const channelData = audioBuffer.getChannelData(0)
        
        const int16Array = new Int16Array(arrayBuffer)
        for (let i = 0; i < numSamples; i++) {
          channelData[i] = int16Array[i] / 32768.0
        }
        
        const source = audioContextRef.current.createBufferSource()
        source.buffer = audioBuffer
        source.connect(audioContextRef.current.destination)
        source.start()
        
        console.log(`🔊 Playing audio: ${numSamples} samples at ${sampleRate}Hz`)
      } else {
        console.warn('⚠️ Empty audio buffer received')
      }
    } catch (error) {
      console.error('❌ Error playing audio chunk:', error)
    }
  }, [])

  // End session
  const endSession = useCallback(() => {
    console.log('🔚 Ending interview session...')
    cleanup()
    onEnd()
  }, [cleanup, onEnd])

  // Start audio recording
  const startRecording = useCallback(async () => {
    if (isRecording || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return
    }

    try {
      console.log('🎤 Starting PCM audio recording...')
      
      // Clear any existing audio queue when user starts speaking (interruption)
      clearAudioQueue()
      
      // Send interruption signal to server
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'user_interruption',
          timestamp: Date.now()
        }))
        console.log('⚡ Sent user interruption signal to server')
      }
      
      // Get user media
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: { 
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true
        } 
      })
      
      audioStreamRef.current = stream
      
      // Setup Web Audio API for raw PCM capture
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({
        sampleRate: 16000 // Match Gemini's expected input rate
      })
      
      const source = audioContextRef.current.createMediaStreamSource(stream)
      
      // Create a ScriptProcessorNode for raw PCM data
      const bufferSize = 4096
      const processor = audioContextRef.current.createScriptProcessor(bufferSize, 1, 1)
      processorRef.current = processor
      
      processor.onaudioprocess = (event) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          const inputBuffer = event.inputBuffer
          const inputData = inputBuffer.getChannelData(0) // Float32Array
          
          // Convert float32 PCM to int16 PCM (what Gemini expects)
          const int16Array = new Int16Array(inputData.length)
          for (let i = 0; i < inputData.length; i++) {
            // Convert from -1.0 to 1.0 range to -32768 to 32767 range
            int16Array[i] = Math.max(-32768, Math.min(32767, inputData[i] * 32767))
          }
          
          // Send raw PCM data directly to websocket_server.py
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(int16Array.buffer)
          }
        }
      }
      
      // Connect the audio processing chain
      source.connect(processor)
      processor.connect(audioContextRef.current.destination)
      
      setIsRecording(true)
      console.log('✅ PCM audio recording started')
      
    } catch (err) {
      console.error('❌ Error starting recording:', err)
      setError(`Failed to start recording: ${err}`)
    }
  }, [isRecording, clearAudioQueue])

  // Stop audio recording
  const stopRecording = useCallback(() => {
    if (!isRecording) return

    console.log('🛑 Stopping audio recording...')
    
    // Stop microphone
    if (audioStreamRef.current) {
      audioStreamRef.current.getTracks().forEach(track => track.stop())
      audioStreamRef.current = null
    }
    
    // Disconnect audio processor
    if (processorRef.current) {
      processorRef.current.disconnect()
      processorRef.current = null
    }
    
    setIsRecording(false)
    console.log('✅ Audio recording stopped')
  }, [isRecording])

  // Send text message
  const sendTextMessage = useCallback((message: string) => {
    if (!wsRef.current || !message.trim()) return

    // Add user message to transcript
    const userEntry: TranscriptEntry = {
      id: `entry_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      speaker: 'user',
      content: message.trim(),
      timestamp: new Date()
    }
    
    setTranscript(prev => [...prev, userEntry])

    // Send to backend
    wsRef.current.send(JSON.stringify({
      type: 'text_message',
      data: {
        session_id: sessionIdRef.current,
        text: message.trim()
      }
    }))
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return cleanup
  }, [cleanup])

  return {
    session,
    transcript,
    isConnected,
    isRecording,
    volumeLevel,
    error,
    startSession,
    endSession,
    startRecording,
    stopRecording,
    sendTextMessage
  }
} 