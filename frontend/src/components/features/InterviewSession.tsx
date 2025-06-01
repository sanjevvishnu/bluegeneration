'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { InterviewPrompt } from '@/types/interview'
import { useInterviewSession } from '@/hooks/useInterviewSession'
import { formatTime } from '@/lib/utils'
import { Mic, MicOff, Volume2, VolumeX, MessageSquare, Send } from 'lucide-react'

interface InterviewSessionProps {
  prompt: InterviewPrompt
  onEnd: () => void
}

export function InterviewSession({ prompt, onEnd }: InterviewSessionProps) {
  const [textInput, setTextInput] = useState('')
  const [isMuted, setIsMuted] = useState(false)
  
  const {
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
  } = useInterviewSession({ prompt, onEnd })

  const handleStartSession = () => {
    startSession()
  }

  const handleSendMessage = () => {
    if (textInput.trim()) {
      sendTextMessage(textInput)
      setTextInput('')
    }
  }

  const getDurationInSeconds = () => {
    if (!session?.startTime) return 0
    const now = session.endTime || new Date()
    return Math.floor((now.getTime() - session.startTime.getTime()) / 1000)
  }

  // Connection status badge
  const connectionStatus = () => {
    if (error) return { variant: 'destructive' as const, text: 'Error' }
    if (!isConnected) return { variant: 'secondary' as const, text: 'Disconnected' }
    if (isRecording) return { variant: 'default' as const, text: 'Recording' }
    return { variant: 'outline' as const, text: 'Connected' }
  }

  // If no session, show start button
  if (!session) {
    return (
      <div className="max-w-2xl mx-auto">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {prompt.name}
              <Badge variant="outline">{prompt.difficulty}</Badge>
            </CardTitle>
            <p className="text-muted-foreground">{prompt.description}</p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-center">
              <Button 
                size="lg" 
                onClick={handleStartSession}
                className="w-full"
              >
                Connect to Interview System
              </Button>
            </div>
            
            <div className="text-xs text-muted-foreground">
              <p>• Ensure microphone access is allowed</p>
              <p>• Make sure the Supabase backend is running on port 3000</p>
              <p>• Use headphones to prevent audio feedback</p>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Session Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <CardTitle>{prompt.name}</CardTitle>
                <Badge variant={connectionStatus().variant}>
                  {connectionStatus().text}
                </Badge>
              </div>
              
              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                <span>Duration: {formatTime(getDurationInSeconds())}</span>
                <span>Company: {prompt.company}</span>
                <span>Type: {prompt.type}</span>
              </div>
            </div>
            
            {/* Controls */}
            <div className="flex items-center gap-2">
              <Button
                variant={isRecording ? "destructive" : "default"}
                size="icon"
                onClick={isRecording ? stopRecording : startRecording}
                disabled={!isConnected || session.status !== 'active'}
              >
                {isRecording ? <Mic className="h-4 w-4" /> : <MicOff className="h-4 w-4" />}
              </Button>
              
              <Button
                variant={isMuted ? "destructive" : "outline"}
                size="icon"
                onClick={() => setIsMuted(!isMuted)}
              >
                {isMuted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
              </Button>
              
              <Button
                variant="destructive"
                onClick={endSession}
              >
                End Interview
              </Button>
            </div>
          </div>
          
          {/* Volume meter */}
          {isRecording && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Mic className="h-4 w-4" />
                <span>Microphone Level</span>
              </div>
              <Progress value={volumeLevel} className="h-2" />
            </div>
          )}
        </CardHeader>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Conversation */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5" />
                Conversation
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {transcript.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <p>Start speaking to begin the interview...</p>
                    {!isConnected && (
                      <p className="text-sm mt-2">Waiting for connection...</p>
                    )}
                  </div>
                ) : (
                  transcript.map((entry) => (
                    <div
                      key={entry.id}
                      className={`flex ${entry.speaker === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-xs lg:max-w-md px-4 py-3 rounded-lg ${
                          entry.speaker === 'user'
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-muted'
                        }`}
                      >
                        <p className="text-sm">{entry.content}</p>
                        <p className="text-xs opacity-70 mt-1">
                          {entry.timestamp.toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  ))
                )}
              </div>
              
              {/* Text input for backup communication */}
              <div className="flex gap-2 mt-4 pt-4 border-t">
                <input
                  type="text"
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                  placeholder="Type a message (backup)"
                  className="flex-1 px-3 py-2 border rounded-md text-sm"
                  onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                  disabled={!isConnected}
                />
                <Button
                  size="icon"
                  onClick={handleSendMessage}
                  disabled={!textInput.trim() || !isConnected}
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Session Info */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Session Status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between text-sm">
                <span>Status:</span>
                <Badge variant={connectionStatus().variant}>
                  {session.status}
                </Badge>
              </div>
              
              <div className="flex justify-between text-sm">
                <span>Connection:</span>
                <span className={isConnected ? 'text-green-600' : 'text-red-600'}>
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              
              <div className="flex justify-between text-sm">
                <span>Recording:</span>
                <span className={isRecording ? 'text-green-600' : 'text-gray-600'}>
                  {isRecording ? 'Active' : 'Inactive'}
                </span>
              </div>
              
              <div className="flex justify-between text-sm">
                <span>Duration:</span>
                <span>{formatTime(getDurationInSeconds())}</span>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Instructions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm text-muted-foreground">
              <p>• Click the microphone to start/stop recording</p>
              <p>• Speak naturally and clearly</p>
              <p>• Use the text input as backup</p>
              <p>• The AI will respond with voice</p>
              <p>• End the session when finished</p>
            </CardContent>
          </Card>
          
          {/* Error display */}
          {error && (
            <Card className="border-red-200 bg-red-50">
              <CardContent className="pt-6">
                <p className="text-sm text-red-600">{error}</p>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={handleStartSession}
                  className="mt-2"
                >
                  Retry Connection
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
} 