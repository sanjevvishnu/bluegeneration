'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { RefreshCw, MessageCircle, Mic, Bot } from "lucide-react"

interface Transcript {
  id: string
  session_id: string
  speaker: string
  text: string
  created_at: string
  provider: string
  confidence_score?: number
}

export default function TranscriptPage() {
  const [sessionId, setSessionId] = useState('')
  const [transcripts, setTranscripts] = useState<Transcript[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchTranscripts = async (id: string) => {
    if (!id.trim()) return

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(
        `http://localhost:3000/api/transcripts/${id}?format=conversation`
      )
      
      if (!response.ok) {
        if (response.status === 404) {
          setError('No transcripts found for this session')
          setTranscripts([])
        } else {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }
        return
      }

      const data = await response.json()
      
      if (data.content) {
        setTranscripts(data.content)
      } else {
        setTranscripts([])
      }
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch transcripts'
      setError(errorMessage)
      console.error('Error fetching transcripts:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = () => {
    if (sessionId) {
      fetchTranscripts(sessionId)
    }
  }

  const getSpeakerIcon = (speaker: string) => {
    switch (speaker.toLowerCase()) {
      case 'user':
        return <Mic className="h-4 w-4" />
      case 'assistant':
        return <Bot className="h-4 w-4" />
      default:
        return <MessageCircle className="h-4 w-4" />
    }
  }

  const getSpeakerColor = (speaker: string) => {
    switch (speaker.toLowerCase()) {
      case 'user':
        return 'bg-blue-100 text-blue-800'
      case 'assistant':
        return 'bg-green-100 text-green-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <Card className="w-full max-w-4xl mx-auto">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageCircle className="h-5 w-5" />
            Transcript Viewer
          </CardTitle>
          <CardDescription>
            View real-time transcripts of interview conversations
          </CardDescription>
          
          <div className="flex flex-col sm:flex-row gap-4 pt-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder="Enter session ID..."
                value={sessionId}
                onChange={(e) => setSessionId(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              />
            </div>
            
            <Button
              onClick={handleRefresh}
              disabled={loading || !sessionId}
              size="sm"
              variant="outline"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </CardHeader>

        <CardContent>
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          )}

          {loading && (
            <div className="flex items-center justify-center p-8">
              <RefreshCw className="h-6 w-6 animate-spin text-gray-500" />
              <span className="ml-2 text-gray-500">Loading transcripts...</span>
            </div>
          )}

          {!loading && transcripts.length > 0 && (
            <>
              <div className="flex justify-between items-center mb-4">
                <Badge variant="outline">
                  {transcripts.length} transcript{transcripts.length !== 1 ? 's' : ''}
                </Badge>
              </div>

              <div className="max-h-96 overflow-auto border rounded-lg p-4 space-y-4">
                {transcripts.map((transcript, index) => (
                  <div key={transcript.id || index} className="flex gap-3">
                    <div className="flex-shrink-0 mt-1">
                      {getSpeakerIcon(transcript.speaker)}
                    </div>
                    
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-2">
                        <Badge
                          className={getSpeakerColor(transcript.speaker)}
                        >
                          {transcript.speaker}
                        </Badge>
                        
                        <span className="text-xs text-gray-500">
                          {new Date(transcript.created_at).toLocaleTimeString()}
                        </span>
                        
                        {transcript.provider && (
                          <Badge variant="secondary" className="text-xs">
                            {transcript.provider}
                          </Badge>
                        )}
                      </div>
                      
                      <p className="text-sm leading-relaxed">
                        {transcript.text}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}

          {!loading && !error && transcripts.length === 0 && sessionId && (
            <div className="text-center py-8 text-gray-500">
              <MessageCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No transcripts found for this session</p>
              <p className="text-sm">Start a conversation to see transcripts appear here</p>
            </div>
          )}

          {!sessionId && (
            <div className="text-center py-8 text-gray-500">
              <MessageCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Enter a session ID to view transcripts</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
} 