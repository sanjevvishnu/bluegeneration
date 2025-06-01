'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { RefreshCw, MessageCircle, Mic, Bot, Download, Copy } from "lucide-react"
import { useToast } from "@/hooks/use-toast"

interface Transcript {
  id: string
  session_id: string
  speaker: string
  text: string
  created_at: string
  provider: string
  confidence_score?: number
}

interface TranscriptViewerProps {
  sessionId?: string
  autoRefresh?: boolean
  refreshInterval?: number
}

export default function TranscriptViewer({ 
  sessionId: initialSessionId, 
  autoRefresh = false, 
  refreshInterval = 3000 
}: TranscriptViewerProps) {
  const [sessionId, setSessionId] = useState(initialSessionId || '')
  const [transcripts, setTranscripts] = useState<Transcript[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [format, setFormat] = useState<'conversation' | 'json' | 'text'>('conversation')
  const { toast } = useToast()

  const fetchTranscripts = async (id: string) => {
    if (!id.trim()) return

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(
        `http://localhost:3000/api/transcripts/${id}?format=${format}`
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
      
      if (format === 'conversation' && data.content) {
        setTranscripts(data.content)
      } else if (format === 'json' && data.content) {
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

  // Auto-refresh functionality
  useEffect(() => {
    if (!autoRefresh || !sessionId) return

    const interval = setInterval(() => {
      fetchTranscripts(sessionId)
    }, refreshInterval)

    return () => clearInterval(interval)
  }, [autoRefresh, sessionId, refreshInterval, format])

  // Initial fetch when sessionId changes
  useEffect(() => {
    if (sessionId) {
      fetchTranscripts(sessionId)
    }
  }, [sessionId, format])

  const handleRefresh = () => {
    if (sessionId) {
      fetchTranscripts(sessionId)
    }
  }

  const copyToClipboard = async () => {
    if (transcripts.length === 0) return

    const text = transcripts
      .map(t => `[${t.created_at}] ${t.speaker}: ${t.text}`)
      .join('\n\n')

    try {
      await navigator.clipboard.writeText(text)
      toast({
        title: "Copied to clipboard",
        description: "Transcript copied successfully",
      })
    } catch (err) {
      toast({
        title: "Copy failed",
        description: "Failed to copy transcript to clipboard",
        variant: "destructive",
      })
    }
  }

  const downloadTranscript = () => {
    if (transcripts.length === 0) return

    const text = transcripts
      .map(t => `[${t.created_at}] ${t.speaker}: ${t.text}`)
      .join('\n\n')

    const blob = new Blob([text], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `transcript-${sessionId}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
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
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'assistant':
        return 'bg-green-100 text-green-800 border-green-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  return (
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
            <Input
              placeholder="Enter session ID..."
              value={sessionId}
              onChange={(e) => setSessionId(e.target.value)}
              className="w-full"
            />
          </div>
          
          <div className="flex gap-2">
            <select
              value={format}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setFormat(e.target.value as typeof format)}
              className="px-3 py-2 border border-border rounded-md text-sm bg-background"
            >
              <option value="conversation">Conversation</option>
              <option value="json">JSON</option>
              <option value="text">Text</option>
            </select>
            
            <Button
              onClick={handleRefresh}
              disabled={loading || !sessionId}
              size="sm"
              variant="outline"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {error && (
          <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4 mb-4">
            <p className="text-destructive text-sm">{error}</p>
          </div>
        )}

        {loading && (
          <div className="flex items-center justify-center p-8">
            <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
            <span className="ml-2 text-muted-foreground">Loading transcripts...</span>
          </div>
        )}

        {!loading && transcripts.length > 0 && (
          <>
            <div className="flex justify-between items-center mb-4">
              <div className="flex items-center gap-2">
                <Badge variant="outline">
                  {transcripts.length} transcript{transcripts.length !== 1 ? 's' : ''}
                </Badge>
                {autoRefresh && (
                  <Badge variant="secondary">
                    Auto-refresh: {refreshInterval / 1000}s
                  </Badge>
                )}
              </div>
              
              <div className="flex gap-2">
                <Button onClick={copyToClipboard} size="sm" variant="outline">
                  <Copy className="h-4 w-4" />
                  Copy
                </Button>
                <Button onClick={downloadTranscript} size="sm" variant="outline">
                  <Download className="h-4 w-4" />
                  Download
                </Button>
              </div>
            </div>

            <ScrollArea className="h-96 w-full border rounded-lg p-4">
              <div className="space-y-4">
                {transcripts.map((transcript, index) => (
                  <div key={transcript.id || index} className="flex gap-3">
                    <div className="flex-shrink-0 mt-1">
                      {getSpeakerIcon(transcript.speaker)}
                    </div>
                    
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-2">
                        <Badge
                          variant="outline"
                          className={getSpeakerColor(transcript.speaker)}
                        >
                          {transcript.speaker}
                        </Badge>
                        
                        <span className="text-xs text-muted-foreground">
                          {new Date(transcript.created_at).toLocaleTimeString()}
                        </span>
                        
                        {transcript.provider && (
                          <Badge variant="secondary" className="text-xs">
                            {transcript.provider}
                          </Badge>
                        )}
                        
                        {transcript.confidence_score && (
                          <Badge variant="outline" className="text-xs">
                            {Math.round(transcript.confidence_score * 100)}%
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
            </ScrollArea>
          </>
        )}

        {!loading && !error && transcripts.length === 0 && sessionId && (
          <div className="text-center py-8 text-muted-foreground">
            <MessageCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No transcripts found for this session</p>
            <p className="text-sm">Start a conversation to see transcripts appear here</p>
          </div>
        )}

        {!sessionId && (
          <div className="text-center py-8 text-muted-foreground">
            <MessageCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>Enter a session ID to view transcripts</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
} 