"use client"

import React, { useState, useEffect, useRef, useCallback } from 'react'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Separator } from "@/components/ui/separator"
import { Switch } from "@/components/ui/switch"
import { Progress } from "@/components/ui/progress"
import { toast } from "sonner"
import { 
  Mic, 
  MicOff, 
  Square, 
  Send, 
  Save, 
  Trash2, 
  Settings, 
  Briefcase,
  User,
  Bot,
  Volume2,
  VolumeX,
  Circle,
  Waves
} from "lucide-react"

interface TranscriptEntry {
  session_id: string
  speaker: 'User' | 'Assistant'
  text: string
  provider: string
  timestamp: string
}

interface Prompt {
  name: string
  description: string
  system_instruction: string
  welcome_message: string
}

interface SessionData {
  session_id: string
  prompts: Record<string, Prompt>
  status: string
}

export function SupabaseInterviewApp() {
  // WebSocket connection
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected')
  
  // Session state
  const [sessionData, setSessionData] = useState<SessionData | null>(null)
  const [currentMode, setCurrentMode] = useState('amazon_interviewer')
  const [useElevenLabs, setUseElevenLabs] = useState(false)
  
  // Recording state
  const [isRecording, setIsRecording] = useState(false)
  const [audioStream, setAudioStream] = useState<MediaStream | null>(null)
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null)
  const [volumeLevel, setVolumeLevel] = useState(0)
  
  // Audio context for volume monitoring
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const volumeIntervalRef = useRef<NodeJS.Timeout | null>(null)
  
  // UI state
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([])
  const [textInput, setTextInput] = useState('')
  const transcriptContainerRef = useRef<HTMLDivElement>(null)
  
  // Generate session ID
  const sessionId = useRef(Math.random().toString(36).substring(7))

  // Audio streaming state
  const [audioChunks, setAudioChunks] = useState<string[]>([])
  const [isPlayingAudio, setIsPlayingAudio] = useState(false)

  // Voice activity detection state
  const [isSpeaking, setIsSpeaking] = useState(false)
  const silenceTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const lastAudioSentRef = useRef<number>(0)

  // Initialize WebSocket connection
  const connectWebSocket = useCallback(() => {
    try {
      setConnectionStatus('connecting')
      const wsUrl = `ws://localhost:3000/ws/${sessionId.current}`
      const websocket = new WebSocket(wsUrl)
      
      websocket.onopen = () => {
        console.log('🔌 WebSocket connected')
        setConnectionStatus('connected')
        setWs(websocket)
        
        // Create session
        websocket.send(JSON.stringify({
          type: 'create_session',
          data: {
            mode: currentMode,
            use_elevenlabs: useElevenLabs
          }
        }))
        
        toast.success('Connected to interview system')
      }
      
      websocket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          handleWebSocketMessage(message)
        } catch (error) {
          console.error('❌ Error parsing WebSocket message:', error)
        }
      }
      
      websocket.onclose = () => {
        console.log('🔌 WebSocket disconnected')
        setConnectionStatus('disconnected')
        setWs(null)
        toast.error('Disconnected from interview system')
      }
      
      websocket.onerror = (error) => {
        console.error('❌ WebSocket error:', error)
        setConnectionStatus('disconnected')
        toast.error('Connection error. Please check if the backend is running.')
      }
      
    } catch (error) {
      console.error('❌ Failed to connect WebSocket:', error)
      setConnectionStatus('disconnected')
      toast.error('Failed to connect. Please check if the backend is running on port 3000.')
    }
  }, [currentMode, useElevenLabs])

  // Handle WebSocket messages
  const handleWebSocketMessage = (message: any) => {
    console.log('🔍 WebSocket message received:', message)
    
    if (!message) {
      console.error('❌ Received undefined WebSocket message')
      return
    }
    
    const { type, data } = message
    
    if (!type) {
      console.error('❌ WebSocket message missing type:', message)
      return
    }
    
    switch (type) {
      case 'session_ready':
        if (data) setSessionData(data)
        break
        
      case 'session_created':
        if (data) {
          toast.success(`Session created: ${data.mode}`)
          console.log('✅ Session created, ready for audio')
        }
        break
        
      case 'audio_started':
        if (data) {
          console.log('🎙️ Live API audio session started')
          toast.success('Live audio session connected')
          setIsRecording(true)
        }
        break
        
      case 'audio_stopped':
        if (data) {
          console.log('🛑 Live API audio session stopped')
          setIsRecording(false)
        }
        break
        
      case 'audio_chunk':
        if (data) {
          handleAudioChunk(data)
        } else {
          console.error('❌ audio_chunk message missing data')
        }
        break
        
      case 'transcript_update':
        if (data) setTranscript(prev => [...prev, data])
        break
        
      case 'error':
        if (data?.message) {
          console.error('❌ Server error:', data.message)
          toast.error(data.message)
        }
        break
        
      default:
        console.warn('⚠️ Unknown message type:', type)
    }
  }

  // Handle audio recording (send to persistent Live API session)
  const startRecording = async () => {
    if (isRecording || !ws || ws.readyState !== WebSocket.OPEN) {
      return
    }

    try {
      // Start the persistent Live API session
      ws.send(JSON.stringify({
        type: 'start_audio',
        data: { session_id: sessionId.current }
      }))
      
      // Start local audio recording
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: { 
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true
        } 
      })
      
      setAudioStream(stream)
      
      // Setup MediaRecorder for streaming to Live API (pure cookbook pattern)
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0 && ws?.readyState === WebSocket.OPEN) {
          // Convert audio to base64 and send to Live API session
          const reader = new FileReader()
          reader.onload = () => {
            const audioData = reader.result as string
            const base64Audio = audioData.split(',')[1]
            
            // Send audio data to Live API (continuous streaming like cookbook)
            ws.send(JSON.stringify({
              type: 'audio_data',
              data: {
                session_id: sessionId.current,
                audio: base64Audio
              }
            }))
          }
          reader.readAsDataURL(event.data)
        }
      }
      
      // Start recording in small chunks for real-time streaming (cookbook pattern)
      mediaRecorder.start(250) // 250ms chunks for low latency
      setMediaRecorder(mediaRecorder)
      
      // Setup volume monitoring
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)()
      const source = audioContextRef.current.createMediaStreamSource(stream)
      analyserRef.current = audioContextRef.current.createAnalyser()
      analyserRef.current.fftSize = 256
      source.connect(analyserRef.current)

      const bufferLength = analyserRef.current.frequencyBinCount
      const dataArray = new Uint8Array(bufferLength)

      const updateVolume = () => {
        if (analyserRef.current) {
          analyserRef.current.getByteFrequencyData(dataArray)
          const average = dataArray.reduce((a, b) => a + b) / bufferLength
          const percentage = (average / 255) * 100
          setVolumeLevel(percentage)
        }
      }

      volumeIntervalRef.current = setInterval(updateVolume, 100)
      
      console.log('🎤 Started recording for Live API session (cookbook pattern)')
      
    } catch (error) {
      console.error('❌ Error starting recording:', error)
      toast.error('Failed to start recording')
    }
  }

  const stopRecording = () => {
    if (!isRecording) return

    try {
      // Stop MediaRecorder
      if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop()
      }
      
      // Stop local recording
      if (audioStream) {
        audioStream.getTracks().forEach(track => track.stop())
        setAudioStream(null)
      }
      
      // Clear volume monitoring
      if (volumeIntervalRef.current) {
        clearInterval(volumeIntervalRef.current)
        volumeIntervalRef.current = null
      }
      
      // Stop the persistent Live API session
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          type: 'stop_audio',
          data: { session_id: sessionId.current }
        }))
      }
      
      console.log('🛑 Stopped recording and Live API session')
      
    } catch (error) {
      console.error('❌ Error stopping recording:', error)
    }
  }

  // Handle streaming audio chunks from Live API
  const handleAudioChunk = (chunk: any) => {
    if (!chunk) {
      console.error('❌ handleAudioChunk called with undefined chunk')
      return
    }
    
    console.log(`🔊 Received audio chunk: ${chunk.audio?.length || 0} chars`)
    
    if (chunk.audio) {
      // Play audio chunk immediately for low latency
      playAudioChunk(chunk.audio)
    } else {
      console.warn('⚠️ Audio chunk missing data:', chunk)
    }
  }

  // Play individual audio chunk
  const playAudioChunk = async (audioBase64: string) => {
    try {
      const audioData = atob(audioBase64)
      const arrayBuffer = new ArrayBuffer(audioData.length)
      const view = new Uint8Array(arrayBuffer)
      
      for (let i = 0; i < audioData.length; i++) {
        view[i] = audioData.charCodeAt(i)
      }

      if (audioContextRef.current) {
        // Handle raw PCM data from Gemini Live API
        // Gemini Live API returns 24kHz, 16-bit, mono PCM
        const sampleRate = 24000
        const channels = 1
        const bytesPerSample = 2 // 16-bit
        const numSamples = arrayBuffer.byteLength / bytesPerSample
        
        // Create audio buffer
        const audioBuffer = audioContextRef.current.createBuffer(channels, numSamples, sampleRate)
        const channelData = audioBuffer.getChannelData(0)
        
        // Convert 16-bit PCM to float32 array
        const int16Array = new Int16Array(arrayBuffer)
        for (let i = 0; i < numSamples; i++) {
          channelData[i] = int16Array[i] / 32768.0 // Convert to -1.0 to 1.0 range
        }
        
        // Play the audio
        const source = audioContextRef.current.createBufferSource()
        source.buffer = audioBuffer
        source.connect(audioContextRef.current.destination)
        source.start()
      }
    } catch (error) {
      console.error('❌ Error playing audio chunk:', error)
    }
  }

  // Send text message
  const sendTextMessage = () => {
    if (!ws || !textInput.trim()) return

    // Add user message to transcript immediately
    const userTranscriptEntry: TranscriptEntry = {
      session_id: sessionId.current,
      speaker: 'User',
      text: textInput.trim(),
      provider: 'user',
      timestamp: new Date().toISOString()
    }
    
    setTranscript(prev => [...prev, userTranscriptEntry])

    // Send to backend
    ws.send(JSON.stringify({
      type: 'text_input',
      data: {
        text: textInput.trim()
      }
    }))

    setTextInput('')
    toast.success('Message sent')
  }

  // Switch interview mode
  const switchMode = (mode: string) => {
    if (ws) {
      ws.send(JSON.stringify({
        type: 'switch_mode',
        data: { mode }
      }))
    }
  }

  // Toggle voice provider
  const toggleVoiceProvider = () => {
    if (ws) {
      ws.send(JSON.stringify({
        type: 'switch_voice',
        data: { use_elevenlabs: !useElevenLabs }
      }))
    }
  }

  // Auto-scroll transcript
  useEffect(() => {
    if (transcriptContainerRef.current) {
      transcriptContainerRef.current.scrollTop = transcriptContainerRef.current.scrollHeight
    }
  }, [transcript])

  // Initialize audio and WebSocket
  useEffect(() => {
    connectWebSocket()
    
    return () => {
      if (ws) {
        ws.close()
      }
      if (volumeIntervalRef.current) {
        clearInterval(volumeIntervalRef.current)
      }
    }
  }, [connectWebSocket])

  const currentPrompt = sessionData?.prompts[currentMode]

  const ConnectionStatusIcon = () => {
    switch (connectionStatus) {
      case 'connected':
        return <Circle className="w-3 h-3 fill-white text-white" />
      case 'disconnected':
        return <Circle className="w-3 h-3 fill-neutral-500 text-neutral-500" />
      case 'connecting':
        return <Circle className="w-3 h-3 fill-neutral-400 text-neutral-400 animate-pulse" />
    }
  }

  return (
    <div className="min-h-screen bg-black">
      {/* Header */}
      <header className="bg-black/90 backdrop-blur-xl border-b border-neutral-800">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Mic className="w-8 h-8 text-white" />
              <h1 className="text-2xl font-semibold text-white">Live Audio Interview Practice</h1>
              <Badge className="bg-neutral-800 text-white border-neutral-700">Supabase Backend</Badge>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-neutral-900 rounded-full border border-neutral-700">
              <ConnectionStatusIcon />
              <span className="text-sm text-neutral-300 capitalize">{connectionStatus}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-[400px_1fr] gap-8">
          {/* Left Panel - Controls */}
          <div className="space-y-6">
            {/* Interview Mode */}
            <Card className="bg-neutral-900 backdrop-blur-xl border-neutral-800 shadow-2xl">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-white">
                  <Briefcase className="w-5 h-5 text-white" />
                  Interview Mode
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {currentPrompt && (
                  <div className="p-4 bg-neutral-800 rounded-lg border border-neutral-700">
                    <div className="font-semibold text-white mb-2">{currentPrompt.name}</div>
                    <div className="text-sm text-neutral-400">{currentPrompt.description}</div>
                  </div>
                )}
                
                <Select value={currentMode} onValueChange={switchMode}>
                  <SelectTrigger className="bg-neutral-800 border-neutral-700 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-neutral-800 border-neutral-700">
                    {sessionData?.prompts && Object.entries(sessionData.prompts).map(([key, prompt]) => (
                      <SelectItem key={key} value={key} className="text-white focus:bg-neutral-700">
                        {prompt.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </CardContent>
            </Card>

            {/* Recording Controls */}
            <Card className="bg-neutral-900 backdrop-blur-xl border-neutral-800 shadow-2xl">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-white">
                  <Waves className="w-5 h-5 text-white" />
                  Audio Recording
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Volume Level */}
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-neutral-400">Microphone Level</span>
                    <span className="text-neutral-400">{Math.round(volumeLevel)}%</span>
                  </div>
                  <Progress 
                    value={volumeLevel} 
                    className="h-2 bg-neutral-800"
                  />
                </div>

                {/* Recording Button */}
                <Button
                  onClick={isRecording ? stopRecording : startRecording}
                  disabled={connectionStatus !== 'connected'}
                  className={`w-full h-16 text-lg font-semibold rounded-xl transition-all duration-300 ${
                    isRecording 
                      ? 'bg-white text-black hover:bg-neutral-200' 
                      : 'bg-white text-black hover:bg-neutral-200'
                  }`}
                >
                  {isRecording ? (
                    <>
                      <Square className="w-6 h-6 mr-2" />
                      Stop Recording
                    </>
                  ) : (
                    <>
                      <Mic className="w-6 h-6 mr-2" />
                      Start Recording
                    </>
                  )}
                </Button>

                {/* Voice Provider Toggle */}
                <div className="flex items-center justify-between p-4 bg-neutral-800 rounded-lg border border-neutral-700">
                  <div className="flex items-center gap-2">
                    <Volume2 className="w-4 h-4 text-white" />
                    <span className="text-white text-sm">Use ElevenLabs Voice</span>
                  </div>
                  <Switch
                    checked={useElevenLabs}
                    onCheckedChange={toggleVoiceProvider}
                    className="data-[state=checked]:bg-white"
                  />
                </div>
              </CardContent>
            </Card>

            {/* Text Input */}
            <Card className="bg-neutral-900 backdrop-blur-xl border-neutral-800 shadow-2xl">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-white">
                  <Send className="w-5 h-5 text-white" />
                  Text Input
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Textarea
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                  placeholder="Type a message to test text-to-speech..."
                  className="bg-neutral-800 border-neutral-700 text-white placeholder-neutral-500 min-h-[100px] resize-none rounded-xl"
                />
                <Button
                  onClick={sendTextMessage}
                  disabled={!textInput.trim() || connectionStatus !== 'connected'}
                  className="w-full bg-white text-black hover:bg-neutral-200 rounded-xl"
                >
                  <Send className="w-4 h-4 mr-2" />
                  Send Message
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Right Panel - Transcript */}
          <Card className="bg-neutral-900 backdrop-blur-xl border-neutral-800 shadow-2xl">
            <CardHeader className="pb-4">
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2 text-white">
                  <User className="w-5 h-5 text-white" />
                  Interview Transcript
                </CardTitle>
                <div className="flex gap-2">
                  <Button 
                    variant="outline" 
                    size="sm"
                    className="border-neutral-700 text-white hover:bg-neutral-800 rounded-xl"
                    onClick={() => setTranscript([])}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div 
                ref={transcriptContainerRef}
                className="h-[600px] overflow-y-auto space-y-4 pr-4 scrollbar-thin scrollbar-track-neutral-800 scrollbar-thumb-neutral-600"
              >
                {transcript.length === 0 ? (
                  <div className="flex items-center justify-center h-full text-neutral-500 text-center">
                    <div>
                      <Bot className="w-12 h-12 mx-auto mb-4 text-neutral-600" />
                      <p>No conversation yet.</p>
                      <p className="text-sm">Start recording or send a message to begin.</p>
                    </div>
                  </div>
                ) : (
                  transcript.map((entry, index) => (
                    <div key={index} className="flex gap-4">
                      <Avatar className="w-8 h-8 border-2 border-neutral-700">
                        <AvatarFallback className={
                          entry.speaker === 'User' 
                            ? 'bg-white text-black' 
                            : 'bg-neutral-700 text-white'
                        }>
                          {entry.speaker === 'User' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex-1 space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-white">{entry.speaker}</span>
                          <Badge 
                            variant="outline" 
                            className="text-xs border-neutral-600 text-neutral-400"
                          >
                            {entry.provider}
                          </Badge>
                          <span className="text-xs text-neutral-500">
                            {new Date(entry.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                        <p className="text-neutral-300 text-sm leading-relaxed">
                          {entry.text}
                        </p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  )
} 