'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { useRouter } from 'next/navigation'
import { useTheme } from 'next-themes'
import { MdMic, MdPlayArrow, MdBusiness, MdCode, MdRocket, MdSchool, MdLightbulb, MdDarkMode, MdLightMode } from 'react-icons/md'

interface InterviewPrompt {
  name: string
  description: string
  system_instruction: string
  welcome_message: string
}

interface PromptsData {
  [key: string]: InterviewPrompt
}

const iconMap: { [key: string]: React.ReactNode } = {
  microsoft_interviewer: <MdBusiness className="text-foreground" />,
  google_interviewer: <MdCode className="text-foreground" />,
  amazon_interviewer: <MdRocket className="text-foreground" />,
  startup_interviewer: <MdLightbulb className="text-foreground" />,
  general_practice: <MdSchool className="text-foreground" />
}

export default function HomePage() {
  const router = useRouter()
  const { theme, setTheme } = useTheme()
  const [prompts, setPrompts] = useState<PromptsData>({})
  const [selectedPrompt, setSelectedPrompt] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    // Load prompts data
    const loadPrompts = async () => {
      try {
        const response = await fetch('/prompts.json')
        const data = await response.json()
        setPrompts(data)
      } catch (error) {
        console.error('Error loading prompts:', error)
        // Fallback data if JSON fails to load
        const fallbackPrompts: PromptsData = {
          "microsoft_interviewer": {
            "name": "Microsoft Technical Interviewer",
            "description": "Professional Microsoft software engineering interview",
            "system_instruction": "You are a senior software engineer and interviewer at Microsoft...",
            "welcome_message": "🚀 Microsoft Interview Mode: Technical interview simulation"
          },
          "google_interviewer": {
            "name": "Google Technical Interviewer", 
            "description": "Google-style software engineering interview",
            "system_instruction": "You are a senior software engineer and interviewer at Google...",
            "welcome_message": "🔍 Google Interview Mode: Algorithm and system design focus"
          },
          "amazon_interviewer": {
            "name": "Amazon Technical Interviewer",
            "description": "Amazon leadership principles and technical interview", 
            "system_instruction": "You are a senior software engineer and interviewer at Amazon...",
            "welcome_message": "📦 Amazon Interview Mode: Technical + Leadership Principles"
          },
          "startup_interviewer": {
            "name": "Startup Technical Interviewer",
            "description": "Fast-paced startup environment interview",
            "system_instruction": "You are a technical lead at a fast-growing startup...",
            "welcome_message": "🚀 Startup Interview Mode: Versatility and problem-solving focus"
          },
          "general_practice": {
            "name": "General Interview Practice",
            "description": "General technical interview practice",
            "system_instruction": "You are an experienced technical interviewer...",
            "welcome_message": "📚 General Practice Mode: Comprehensive interview preparation"
          }
        }
        setPrompts(fallbackPrompts)
      } finally {
        setLoading(false)
      }
    }

    loadPrompts()
  }, [])

  const handleStartInterview = () => {
    if (selectedPrompt) {
      router.push(`/interview?prompt=${selectedPrompt}`)
    }
  }

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark')
  }

  const selectedPromptData = selectedPrompt ? prompts[selectedPrompt] : null

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="w-96">
          <CardContent className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-border mx-auto mb-4"></div>
            <p className="text-foreground">Loading interview modes...</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      {/* Theme Toggle */}
      <div className="flex justify-end mb-4">
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

      {/* Header */}
      <div className="text-center mb-8">
        <div className="flex items-center justify-center gap-3 mb-4">
          <MdMic className="text-4xl text-foreground" />
          <h1 className="text-4xl font-bold text-foreground">
            AI Interview Practice
          </h1>
        </div>
        <p className="text-xl text-muted-foreground">
          Practice technical interviews with AI-powered interviewers
        </p>
      </div>

      {/* Features Card */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="text-2xl">Features</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center gap-3">
              <Badge variant="outline">Voice</Badge>
              <span className="text-foreground">Real-time voice conversation with AI</span>
            </div>
            <div className="flex items-center gap-3">
              <Badge variant="outline">Modes</Badge>
              <span className="text-foreground">Multiple interview formats</span>
            </div>
            <div className="flex items-center gap-3">
              <Badge variant="outline">Technical</Badge>
              <span className="text-foreground">Technical and behavioral questions</span>
            </div>
            <div className="flex items-center gap-3">
              <Badge variant="outline">Feedback</Badge>
              <span className="text-foreground">Instant feedback and tips</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Interview Mode Selection */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="text-2xl">Choose Interview Mode</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <Select value={selectedPrompt} onValueChange={setSelectedPrompt}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select an interview mode..." />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(prompts).map(([key, prompt]) => (
                <SelectItem key={key} value={key}>
                  <div className="flex items-center gap-2">
                    {iconMap[key]}
                    {prompt.name}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {selectedPromptData && (
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-start gap-3 mb-3">
                  {iconMap[selectedPrompt]}
                  <h3 className="text-xl font-semibold text-foreground">{selectedPromptData.name}</h3>
                </div>
                <p className="text-muted-foreground mb-3">
                  {selectedPromptData.description}
                </p>
                <Separator className="my-3" />
                <p className="text-sm italic text-foreground">
                  {selectedPromptData.welcome_message}
                </p>
              </CardContent>
            </Card>
          )}

          <Button
            size="lg"
            className="w-full"
            disabled={!selectedPrompt}
            onClick={handleStartInterview}
          >
            <MdPlayArrow className="mr-2 h-4 w-4" />
            Start Interview
          </Button>
        </CardContent>
      </Card>

      {/* Tips */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-2 mb-3">
            <MdLightbulb className="text-foreground" />
            <h3 className="font-semibold text-foreground">Tips for Best Experience</h3>
          </div>
          <ul className="text-sm text-muted-foreground space-y-1">
            <li>• Use headphones to prevent audio feedback</li>
            <li>• Ensure a quiet environment for best audio quality</li>
            <li>• Allow microphone access when prompted</li>
            <li>• Speak clearly and at a moderate pace</li>
            <li>• Have a stable internet connection</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  )
} 