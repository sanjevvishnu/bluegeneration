'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useInterviewSession } from '@/hooks/useInterviewSession'
import { Save, Download, List, Clock, MessageSquare } from 'lucide-react'

interface SavedTranscript {
  session_id: string
  created_at: string
  total_entries: number
  duration: number
  filename: string
}

interface TranscriptManagerProps {
  currentTranscript: any[]
  sessionId?: string
}

export function TranscriptManager({ currentTranscript, sessionId }: TranscriptManagerProps) {
  const [savedTranscripts, setSavedTranscripts] = useState<SavedTranscript[]>([])
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)

  const { saveTranscriptToAPI, listTranscriptsFromAPI, getTranscriptFromAPI } = useInterviewSession({
    prompt: null,
    onEnd: () => {}
  })

  // Load saved transcripts on component mount
  useEffect(() => {
    loadTranscripts()
  }, [])

  const loadTranscripts = async () => {
    try {
      setLoading(true)
      const result = await listTranscriptsFromAPI()
      setSavedTranscripts(result.transcripts || [])
    } catch (error) {
      console.error('Failed to load transcripts:', error)
    } finally {
      setLoading(false)
    }
  }

  const saveCurrentTranscript = async () => {
    if (!currentTranscript || currentTranscript.length === 0) {
      alert('No transcript to save')
      return
    }

    try {
      setSaving(true)
      const result = await saveTranscriptToAPI(sessionId)
      if (result) {
        alert('Transcript saved successfully!')
        await loadTranscripts() // Refresh list
      }
    } catch (error) {
      console.error('Failed to save transcript:', error)
      alert('Failed to save transcript')
    } finally {
      setSaving(false)
    }
  }

  const downloadTranscript = async (transcriptSessionId: string) => {
    try {
      const result = await getTranscriptFromAPI(transcriptSessionId)
      
      // Create downloadable content
      const content = result.transcript.map((entry: any) => 
        `[${new Date(entry.timestamp * 1000).toLocaleTimeString()}] ${entry.speaker.toUpperCase()}: ${entry.content}`
      ).join('\n')
      
      const blob = new Blob([content], { type: 'text/plain' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `transcript_${transcriptSessionId}.txt`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Failed to download transcript:', error)
      alert('Failed to download transcript')
    }
  }

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = Math.floor(seconds % 60)
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
  }

  return (
    <div className="space-y-4">
      {/* Current Session Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Save className="h-5 w-5" />
            Current Session
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="text-sm text-muted-foreground">
              {currentTranscript?.length || 0} transcript entries
            </div>
            <Button 
              onClick={saveCurrentTranscript}
              disabled={saving || !currentTranscript || currentTranscript.length === 0}
              size="sm"
            >
              {saving ? 'Saving...' : 'Save Transcript'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Saved Transcripts */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <List className="h-5 w-5" />
            Saved Transcripts
            <Badge variant="secondary">{savedTranscripts.length}</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-4 text-muted-foreground">
              Loading transcripts...
            </div>
          ) : savedTranscripts.length === 0 ? (
            <div className="text-center py-4 text-muted-foreground">
              No saved transcripts yet
            </div>
          ) : (
            <div className="space-y-3">
              {savedTranscripts.map((transcript) => (
                <div
                  key={transcript.session_id}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div className="space-y-1">
                    <div className="text-sm font-medium">
                      Session: {transcript.session_id.slice(-8)}
                    </div>
                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {formatDuration(transcript.duration)}
                      </div>
                      <div className="flex items-center gap-1">
                        <MessageSquare className="h-3 w-3" />
                        {transcript.total_entries} entries
                      </div>
                      <div>
                        {new Date(transcript.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                  <Button
                    onClick={() => downloadTranscript(transcript.session_id)}
                    size="sm"
                    variant="outline"
                  >
                    <Download className="h-4 w-4 mr-1" />
                    Download
                  </Button>
                </div>
              ))}
            </div>
          )}
          
          <div className="pt-4 border-t">
            <Button 
              onClick={loadTranscripts}
              variant="outline" 
              size="sm"
              disabled={loading}
            >
              {loading ? 'Refreshing...' : 'Refresh List'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 