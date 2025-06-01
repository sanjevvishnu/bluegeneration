"use client"

import React, { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { AlertCircle, Mic, MicOff, Square, Settings } from 'lucide-react'
import { Alert, AlertDescription } from "@/components/ui/alert"
import { useInterviewSession } from '@/hooks/useInterviewSession'
import { useUser } from '@clerk/nextjs'

// Types  
interface InterviewPrompt {
  id: string
  name: string
  description: string
  category: string
  systemInstruction: string
}

export default function SupabaseInterviewApp() {
  const { user } = useUser()
  const [selectedPrompt, setSelectedPrompt] = useState<InterviewPrompt | null>(null)
  const [availablePrompts, setAvailablePrompts] = useState<InterviewPrompt[]>([])
  const [loadingPrompts, setLoadingPrompts] = useState(true)
  const [promptError, setPromptError] = useState<string | null>(null)

  const {
    isConnected,
    isRecording,
    transcript,
    error,
    startSession,
    endSession,
    startRecording,
    stopRecording
  } = useInterviewSession({
    prompt: selectedPrompt,
    userId: user?.id,
    onEnd: () => {
      console.log('Interview session ended')
    }
  })

  // Add debugging for session start
  const handleStartSession = () => {
    console.log('🚀 User clicked Start Interview Session button')
    console.log('📋 Selected prompt:', selectedPrompt)
    console.log('👤 User ID:', user?.id)
    startSession()
  }

  // Debug logs for state changes
  useEffect(() => {
    console.log('🔄 Interview app state changed:', {
      isConnected,
      selectedPrompt: selectedPrompt?.id,
      userId: user?.id
    })
  }, [isConnected, selectedPrompt, user?.id])

  // Fetch prompts from backend API on component mount
  useEffect(() => {
    const fetchPrompts = async () => {
      try {
        setLoadingPrompts(true)
        setPromptError(null)
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000'
        const response = await fetch(`${apiUrl}/api/prompts`)
        
        if (response.ok) {
          const backendPrompts = await response.json()
          
          // Convert backend prompts format to frontend format
          const formattedPrompts: InterviewPrompt[] = Object.entries(backendPrompts).map(([id, prompt]: [string, any]) => ({
            id,
            name: prompt.name,
            description: prompt.description,
            category: 'Interview', // You can categorize these as needed
            systemInstruction: prompt.system_instruction
          }))
          
          setAvailablePrompts(formattedPrompts)
          console.log('✅ Loaded prompts from backend:', formattedPrompts)
        } else {
          throw new Error(`Backend responded with status ${response.status}`)
        }
      } catch (error) {
        console.error('❌ Error fetching prompts:', error)
        setPromptError('Could not load interview types. Make sure the backend is running on port 3000.')
        setAvailablePrompts([]) // No fallback prompts
      } finally {
        setLoadingPrompts(false)
      }
    }

    fetchPrompts()
  }, [])

  const retryFetchPrompts = () => {
    setLoadingPrompts(true)
    setPromptError(null)
    // Re-run the fetch logic
    const fetchPrompts = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000'
        const response = await fetch(`${apiUrl}/api/prompts`)
        
        if (response.ok) {
          const backendPrompts = await response.json()
          
          const formattedPrompts: InterviewPrompt[] = Object.entries(backendPrompts).map(([id, prompt]: [string, any]) => ({
            id,
            name: prompt.name,
            description: prompt.description,
            category: 'Interview',
            systemInstruction: prompt.system_instruction
          }))
          
          setAvailablePrompts(formattedPrompts)
          console.log('✅ Retry: Loaded prompts from backend:', formattedPrompts)
        } else {
          throw new Error(`Backend responded with status ${response.status}`)
        }
      } catch (error) {
        console.error('❌ Retry failed:', error)
        setPromptError('Could not load interview types. Make sure the backend is running on port 3000.')
        setAvailablePrompts([])
      } finally {
        setLoadingPrompts(false)
      }
    }
    
    fetchPrompts()
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="mx-auto max-w-4xl space-y-6">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Coimbatore Interview Assistant
          </h1>
          <p className="text-xl text-gray-600">
            Practice interviews with real-time voice conversation
          </p>
        </div>

        {/* Error Display */}
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Prompt Selection */}
        {!isConnected && (
          <Card>
            <CardHeader>
              <CardTitle>Choose Interview Type</CardTitle>
              <CardDescription>
                {loadingPrompts 
                  ? "Loading interview types from backend..." 
                  : promptError 
                    ? "Backend connection failed"
                    : availablePrompts.length === 0
                    ? "No interview types available"
                    : "Select the type of interview you'd like to practice"
                }
              </CardDescription>
            </CardHeader>
            <CardContent>
              {promptError && (
                <Alert className="mb-4">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    {promptError}
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={retryFetchPrompts}
                      className="ml-2"
                    >
                      Retry
                    </Button>
                  </AlertDescription>
                </Alert>
              )}
              
              {loadingPrompts ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
                  <p className="text-sm text-gray-600 mt-2">Loading interview types...</p>
                </div>
              ) : availablePrompts.length === 0 && !promptError ? (
                <div className="text-center py-8">
                  <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 mb-4">No interview types found</p>
                  <Button onClick={retryFetchPrompts}>
                    Reload Interview Types
                  </Button>
                </div>
              ) : availablePrompts.length === 0 && promptError ? (
                <div className="text-center py-8">
                  <AlertCircle className="h-12 w-12 text-red-400 mx-auto mb-4" />
                  <p className="text-gray-600 mb-4">Unable to load interview types</p>
                  <div className="space-y-2">
                    <p className="text-sm text-gray-500">Make sure the backend is running:</p>
                    <code className="bg-gray-100 px-2 py-1 rounded text-sm">
                      cd backend && python simple_supabase_backend.py
                    </code>
                  </div>
                </div>
              ) : (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {availablePrompts.map((prompt) => (
                      <Card
                        key={prompt.id}
                        className={`cursor-pointer transition-all hover:shadow-md ${
                          selectedPrompt?.id === prompt.id
                            ? 'ring-2 ring-blue-500 bg-blue-50'
                            : 'hover:bg-gray-50'
                        }`}
                        onClick={() => setSelectedPrompt(prompt)}
                      >
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <h3 className="font-semibold text-sm">{prompt.name}</h3>
                              <p className="text-xs text-gray-600 mt-1">
                                {prompt.description}
                              </p>
                            </div>
                            <Badge variant="secondary" className="text-xs">
                              {prompt.category}
                            </Badge>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                  
                  <div className="mt-6 flex justify-center">
                    <Button
                      onClick={handleStartSession}
                      disabled={!selectedPrompt}
                      size="lg"
                      className="px-8"
                    >
                      Start Interview Session
                    </Button>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        )}

        {/* Interview Session */}
        {isConnected && (
          <div className="space-y-6">
            {/* Session Status */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                  Interview Session Active
                </CardTitle>
                <CardDescription>
                  {selectedPrompt?.name}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-4">
                <Button
                  onClick={isRecording ? stopRecording : startRecording}
                    variant={isRecording ? "destructive" : "default"}
                    size="lg"
                    className="flex items-center gap-2"
                >
                  {isRecording ? (
                    <>
                        <MicOff className="w-5 h-5" />
                      Stop Recording
                    </>
                  ) : (
                    <>
                        <Mic className="w-5 h-5" />
                      Start Recording
                    </>
                  )}
                </Button>

                  <Button
                    onClick={endSession}
                    variant="outline"
                    size="lg"
                    className="flex items-center gap-2"
                  >
                    <Square className="w-5 h-5" />
                    End Session
                  </Button>
                </div>
                
                {isRecording && (
                  <div className="mt-4 p-4 bg-red-50 rounded-lg border border-red-200">
                    <div className="flex items-center gap-2 text-red-700">
                      <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                      <span className="text-sm font-medium">Recording in progress...</span>
                    </div>
                    <p className="text-xs text-red-600 mt-1">
                      Speak clearly into your microphone. The AI will respond automatically.
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Transcript */}
            <Card>
              <CardHeader>
                <CardTitle>Interview Transcript</CardTitle>
                <CardDescription>
                  Real-time conversation history
                </CardDescription>
            </CardHeader>
            <CardContent>
                <div className="space-y-4 max-h-96 overflow-y-auto">
                {transcript.length === 0 ? (
                    <p className="text-gray-500 text-center py-8">
                      Transcript will appear here as you speak...
                    </p>
                  ) : (
                    transcript.map((entry) => (
                      <div
                        key={entry.id}
                        className={`p-3 rounded-lg ${
                          entry.speaker === 'user'
                            ? 'bg-blue-50 border-l-4 border-blue-500'
                            : 'bg-gray-50 border-l-4 border-gray-500'
                        }`}
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <Badge variant={entry.speaker === 'user' ? 'default' : 'secondary'}>
                            {entry.speaker === 'user' ? 'User' : 'Assistant'}
                          </Badge>
                          <span className="text-xs text-gray-500">
                            {entry.timestamp.toLocaleTimeString()}
                          </span>
                        </div>
                        <p className="text-sm">{entry.content}</p>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </div>
        )}

        {/* Instructions */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="w-5 h-5" />
              How It Works
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <h4 className="font-semibold mb-2">Setup:</h4>
                <ul className="space-y-1 text-gray-600">
                  <li>• Choose an interview type</li>
                  <li>• Click "Start Interview Session"</li>
                  <li>• Allow microphone access</li>
                  <li>• Test your audio setup</li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold mb-2">During Interview:</h4>
                <ul className="space-y-1 text-gray-600">
                  <li>• Speak naturally and clearly</li>
                  <li>• You can interrupt the AI anytime</li>
                  <li>• Real-time voice conversation</li>
                  <li>• Review transcript in real-time</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
} 