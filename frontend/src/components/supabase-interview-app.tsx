"use client"

import React, { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { AlertCircle, Mic, MicOff, Square, Settings } from 'lucide-react'
import { Alert, AlertDescription } from "@/components/ui/alert"
import { useInterviewSession } from '@/hooks/useInterviewSession'

// Types  
interface InterviewPrompt {
  id: string
  name: string
  description: string
  category: string
  systemInstruction: string
}

const AVAILABLE_PROMPTS: InterviewPrompt[] = [
  {
    id: 'technical_screening',
    name: 'Technical Screening',
    description: 'General software engineering interview questions',
    category: 'Technical',
    systemInstruction: 'You are a technical interviewer for software engineering positions.'
  },
  {
    id: 'algorithms_data_structures',
    name: 'Algorithms & Data Structures',
    description: 'Focus on algorithmic thinking and problem-solving',
    category: 'Technical',
    systemInstruction: 'You are an expert interviewer focusing on algorithms and data structures.'
  },
  {
    id: 'system_design',
    name: 'System Design',
    description: 'Large-scale system architecture and design',
    category: 'Technical',
    systemInstruction: 'You are a senior engineer interviewer focusing on system design and architecture.'
  },
  {
    id: 'behavioral',
    name: 'Behavioral Interview',
    description: 'Leadership, teamwork, and cultural fit questions',
    category: 'Behavioral',
    systemInstruction: 'You are a hiring manager conducting behavioral interviews.'
  },
  {
    id: 'frontend_specialist',
    name: 'Frontend Specialist',
    description: 'React, JavaScript, CSS, and frontend best practices',
    category: 'Technical',
    systemInstruction: 'You are a frontend engineering expert interviewer.'
  }
]

export default function SupabaseInterviewApp() {
  const [selectedPrompt, setSelectedPrompt] = useState<InterviewPrompt | null>(null)

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
    onEnd: () => {
      console.log('Interview session ended')
    }
  })

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="mx-auto max-w-4xl space-y-6">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            AI Interview Assistant
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
                Select the type of interview you'd like to practice
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {AVAILABLE_PROMPTS.map((prompt) => (
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
                  onClick={startSession}
                  disabled={!selectedPrompt}
                  size="lg"
                  className="px-8"
                >
                  Start Interview Session
                </Button>
              </div>
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