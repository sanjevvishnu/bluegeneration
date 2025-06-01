// Interview-related TypeScript types

export interface InterviewPrompt {
  id: string
  name: string
  description: string
  systemInstruction: string
  difficulty?: string
  company?: string
  type?: string
}

export interface TranscriptEntry {
  id: string
  speaker: 'user' | 'ai'
  content: string
  timestamp: Date
}

export interface InterviewSession {
  id: string
  promptId: string
  startTime: Date
  endTime?: Date
  status: 'connecting' | 'active' | 'completed'
  transcript: TranscriptEntry[]
}

export interface WebSocketMessage {
  type: string
  data?: any
}

export interface UseInterviewSessionProps {
  prompt: InterviewPrompt | null
  onEnd: () => void
}

export interface UseInterviewSessionReturn {
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
  requestFullTranscript: () => void
  saveTranscriptToAPI: (sessionId?: string) => Promise<any>
  getTranscriptFromAPI: (sessionId: string) => Promise<any>
  listTranscriptsFromAPI: () => Promise<any>
}

// Audio-related types
export interface AudioQueueItem {
  data: ArrayBuffer
  timestamp: number
  id: string
}

// Additional types for completeness
export interface InterviewSettings {
  recordingEnabled: boolean
  voiceActivityDetection: boolean
  audioQuality: 'low' | 'medium' | 'high'
}

export interface SessionStats {
  duration: number
  totalMessages: number
  audioChunks: number
  averageResponseTime: number
} 