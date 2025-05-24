'use client'

import React, { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import { useRouter, useSearchParams } from 'next/navigation'
import { useTheme } from 'next-themes'
import { MdMic, MdMicOff, MdArrowBack, MdVolumeUp, MdSettings, MdDarkMode, MdLightMode } from 'react-icons/md'

interface InterviewPrompt {
  name: string
  description: string
  system_instruction: string
  welcome_message: string
}

interface PromptsData {
  [key: string]: InterviewPrompt
}

export default function InterviewPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { theme, setTheme } = useTheme()
  const [isRecording, setIsRecording] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [currentPrompt, setCurrentPrompt] = useState<InterviewPrompt | null>(null)
  const [debugInfo, setDebugInfo] = useState<string>('Ready to connect')
  const [audioLevel, setAudioLevel] = useState(0)
  const [mounted, setMounted] = useState(false)
  
  // Audio context refs
  const wsRef = useRef<WebSocket | null>(null)
  const recordingContextRef = useRef<AudioContext | null>(null)
  const playbackContextRef = useRef<AudioContext | null>(null)
  const processorRef = useRef<ScriptProcessorNode | null>(null)
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  
  // Audio queue for playback
  const audioQueueRef = useRef<AudioBuffer[]>([])
  const isPlayingRef = useRef(false)
  const nextPlayTimeRef = useRef(0)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    const promptKey = searchParams?.get('prompt')
    
    if (!promptKey) {
      router.push('/')
      return
    }

    // Load prompt data
    const loadPrompt = async () => {
      try {
        const response = await fetch('/prompts.json')
        const prompts: PromptsData = await response.json()
        
        if (prompts[promptKey]) {
          setCurrentPrompt(prompts[promptKey])
        } else {
          router.push('/')
        }
      } catch (error) {
        console.error('Error loading prompt:', error)
        router.push('/')
      }
    }

    loadPrompt()
  }, [searchParams, router])

  const updateDebug = (message: string) => {
    console.log(message)
    setDebugInfo(message)
  }

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark')
  }

  const connectWebSocket = () => {
    const ws = new WebSocket('ws://localhost:8765')
    wsRef.current = ws

    ws.onopen = () => {
      setIsConnected(true)
      updateDebug('Connected to server')
      
      // Send prompt selection
      if (currentPrompt) {
        ws.send(JSON.stringify({
          type: 'prompt_selection',
          prompt: searchParams?.get('prompt')
        }))
        updateDebug('Sent prompt configuration')
      }
    }

    ws.onmessage = async (event) => {
      if (typeof event.data === 'string') {
        try {
          const message = JSON.parse(event.data)
          if (message.type === 'prompt_configured') {
            updateDebug(`Interview mode configured: ${message.prompt}`)
          }
        } catch (e) {
          updateDebug(`Server message: ${event.data}`)
        }
        return
      }

      // Handle audio data
      if (event.data instanceof ArrayBuffer) {
        await queueAudioChunk(event.data)
      } else if (event.data instanceof Blob) {
        const buffer = await event.data.arrayBuffer()
        await queueAudioChunk(buffer)
      }
    }

    ws.onerror = (error) => {
      updateDebug('WebSocket error')
      console.error('WebSocket error:', error)
    }

    ws.onclose = () => {
      setIsConnected(false)
      updateDebug('Disconnected from server')
    }
  }

  const startRecording = async () => {
    try {
      updateDebug('Requesting microphone access...')
      
      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: false
        }
      })
      
      streamRef.current = stream
      updateDebug('Microphone access granted')

      // Connect WebSocket if not connected
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        connectWebSocket()
      }

      // Set up recording audio context
      recordingContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({
        sampleRate: 16000
      })
      
      // Set up playback context FIRST and resume it
      playbackContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)()
      
      if (playbackContextRef.current.state === 'suspended') {
        await playbackContextRef.current.resume()
        updateDebug('Audio playback context resumed')
      }
      
      sourceRef.current = recordingContextRef.current.createMediaStreamSource(stream)
      processorRef.current = recordingContextRef.current.createScriptProcessor(4096, 1, 1)
      
      processorRef.current.onaudioprocess = (event) => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          const inputBuffer = event.inputBuffer
          const channelData = inputBuffer.getChannelData(0)
          
          // Calculate audio level for visualization
          let sum = 0
          for (let i = 0; i < channelData.length; i++) {
            sum += channelData[i] * channelData[i]
          }
          const rms = Math.sqrt(sum / channelData.length)
          setAudioLevel(Math.min(rms * 100, 100))
          
          // Convert to PCM and send
          const pcmSamples = new Int16Array(channelData.length)
          for (let i = 0; i < channelData.length; i++) {
            const sample = Math.max(-1, Math.min(1, channelData[i]))
            pcmSamples[i] = sample * 32767
          }
          
          wsRef.current.send(pcmSamples.buffer)
        }
      }
      
      // Connect audio nodes
      sourceRef.current.connect(processorRef.current)
      processorRef.current.connect(recordingContextRef.current.destination)
      
      setIsRecording(true)
      updateDebug('Recording started - Audio playback ready')
    } catch (error) {
      updateDebug(`Error starting recording: ${error}`)
      console.error('Error starting recording:', error)
    }
  }

  const stopRecording = () => {
    setIsRecording(false)
    updateDebug('Recording stopped')
    
    // Clean up audio recording
    if (processorRef.current) {
      processorRef.current.disconnect()
      processorRef.current = null
    }
    
    if (sourceRef.current) {
      sourceRef.current.disconnect()
      sourceRef.current = null
    }
    
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }
    
    if (recordingContextRef.current && recordingContextRef.current.state !== 'closed') {
      recordingContextRef.current.close()
      recordingContextRef.current = null
    }
    
    // Close WebSocket
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.close()
    }
    
    setAudioLevel(0)
  }

  const queueAudioChunk = async (audioData: ArrayBuffer) => {
    try {
      if (!playbackContextRef.current) {
        updateDebug('❌ No playback context available')
        return
      }
      
      const samples = new Int16Array(audioData)
      if (samples.length === 0) {
        updateDebug('❌ Empty audio data received')
        return
      }
      
      updateDebug(`🎵 Processing audio chunk: ${samples.length} samples`)
      
      // Convert Int16 PCM to Float32
      const floatSamples = new Float32Array(samples.length)
      for (let i = 0; i < samples.length; i++) {
        floatSamples[i] = samples[i] / 32768.0
      }
      
      // Create audio buffer at 24kHz
      const audioBuffer = playbackContextRef.current.createBuffer(1, floatSamples.length, 24000)
      audioBuffer.getChannelData(0).set(floatSamples)
      
      // Add to queue
      audioQueueRef.current.push(audioBuffer)
      updateDebug(`🔊 Queued audio: ${audioQueueRef.current.length} chunks total`)
      
      // Start playing if not already playing
      if (!isPlayingRef.current) {
        updateDebug('🎬 Starting audio playback')
        playNextChunk()
      }
    } catch (error) {
      console.error('Error queueing audio:', error)
      updateDebug(`❌ Audio queue error: ${error}`)
    }
  }

  const playNextChunk = async () => {
    if (audioQueueRef.current.length === 0) {
      isPlayingRef.current = false
      updateDebug('🔇 Audio queue empty, stopping playback')
      return
    }
    
    if (!playbackContextRef.current) {
      updateDebug('❌ No playback context for audio playback')
      return
    }
    
    isPlayingRef.current = true
    const audioBuffer = audioQueueRef.current.shift()!
    
    try {
      const sourceNode = playbackContextRef.current.createBufferSource()
      sourceNode.buffer = audioBuffer
      
      const gainNode = playbackContextRef.current.createGain()
      gainNode.gain.value = 0.8  // 80% volume
      
      sourceNode.connect(gainNode)
      gainNode.connect(playbackContextRef.current.destination)
      
      const currentTime = playbackContextRef.current.currentTime
      const startTime = Math.max(currentTime, nextPlayTimeRef.current)
      const duration = audioBuffer.length / audioBuffer.sampleRate
      nextPlayTimeRef.current = startTime + duration
      
      updateDebug(`🎵 Playing audio chunk: ${duration.toFixed(2)}s`)
      sourceNode.start(startTime)
      
      sourceNode.onended = () => {
        updateDebug('🎵 Audio chunk finished')
        playNextChunk()
      }
    } catch (error) {
      console.error('Error playing audio:', error)
      updateDebug(`❌ Audio playback error: ${error}`)
      playNextChunk()
    }
  }

  const playTestTone = async () => {
    try {
      if (!playbackContextRef.current) {
        playbackContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)()
      }
      
      if (playbackContextRef.current.state === 'suspended') {
        await playbackContextRef.current.resume()
      }
      
      // Create a 440Hz test tone for 1 second
      const oscillator = playbackContextRef.current.createOscillator()
      const gainNode = playbackContextRef.current.createGain()
      
      oscillator.connect(gainNode)
      gainNode.connect(playbackContextRef.current.destination)
      
      oscillator.frequency.value = 440 // A4 note
      gainNode.gain.value = 0.1 // Low volume
      
      oscillator.start()
      oscillator.stop(playbackContextRef.current.currentTime + 0.5) // Play for 0.5 seconds
      
      updateDebug('🔊 Test tone played')
    } catch (error) {
      updateDebug(`❌ Test tone error: ${error}`)
    }
  }

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording()
    } else {
      startRecording()
    }
  }

  if (!currentPrompt) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="w-96">
          <CardContent className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-border mx-auto mb-4"></div>
            <p className="text-foreground">Loading interview mode...</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Button
            variant="outline"
            size="icon"
            onClick={() => router.push('/')}
          >
            <MdArrowBack className="h-4 w-4" />
          </Button>
          <h1 className="text-2xl font-bold text-foreground">AI Interview Practice</h1>
        </div>
        {mounted && (
          <Button
            variant="outline"
            size="icon"
            onClick={toggleTheme}
          >
            {theme === 'dark' ? 
              <MdLightMode className="h-4 w-4" /> : 
              <MdDarkMode className="h-4 w-4" />
            }
          </Button>
        )}
      </div>

      {/* Interview Mode Info */}
      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center justify-between w-full">
            <CardTitle className="text-xl">{currentPrompt.name}</CardTitle>
            <Badge variant={isConnected ? "default" : "outline"}>
              {isConnected ? "Connected" : "Disconnected"}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground mb-3">
            {currentPrompt.description}
          </p>
          <Separator className="my-3" />
          <p className="text-sm italic text-foreground">
            {currentPrompt.welcome_message}
          </p>
        </CardContent>
      </Card>

      {/* Recording Controls */}
      <Card className="mb-6">
        <CardContent className="text-center py-8">
          <div className="space-y-6">
            <Button
              size="lg"
              variant={isRecording ? "default" : "outline"}
              className="w-40 h-40 rounded-full text-base"
              onClick={toggleRecording}
            >
              <div className="flex flex-col items-center gap-2">
                {isRecording ? <MdMicOff className="text-4xl" /> : <MdMic className="text-4xl" />}
                <span className="text-sm">
                  {isRecording ? "Stop" : "Start"} Interview
                </span>
              </div>
            </Button>
            
            {isRecording && (
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">Audio Level</p>
                <div className="max-w-md mx-auto">
                  <Progress value={audioLevel} className="w-full" />
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Debug Info */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <MdSettings className="h-4 w-4" />
            <CardTitle className="text-base">Debug Information</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm font-mono text-muted-foreground">
            {debugInfo}
          </p>
        </CardContent>
      </Card>
    </div>
  )
} 