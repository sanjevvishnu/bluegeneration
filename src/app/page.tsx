'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { useRouter } from 'next/navigation'
import FloatingNavbar from '@/components/FloatingNavbar'
import { 
  MdMic, 
  MdPlayArrow, 
  MdBusiness, 
  MdCode, 
  MdRocket, 
  MdSchool, 
  MdLightbulb,
  MdSpeed,
  MdFeedback,
  MdTrendingUp,
  MdStar,
  MdCheckCircle
} from 'react-icons/md'

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
  const [prompts, setPrompts] = useState<PromptsData>({})
  const [selectedPrompt, setSelectedPrompt] = useState<string>('')
  const [loading, setLoading] = useState(true)

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
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      <FloatingNavbar 
        onStartInterview={handleStartInterview}
        hasInterviewSelected={!!selectedPrompt}
      />

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4">
        <div className="container mx-auto max-w-6xl text-center">
          <div className="mb-8">
            <Badge className="mb-4 px-3 py-1 text-sm">
              ✨ AI-Powered Interview Practice
            </Badge>
            <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-foreground to-muted-foreground bg-clip-text text-transparent">
              Ace Your Next
              <br />
              <span className="text-primary">Tech Interview</span>
            </h1>
            <p className="text-xl md:text-2xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
              Practice with AI interviewers from top tech companies. Get real-time feedback, 
              improve your skills, and land your dream job.
            </p>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
            <Button size="lg" className="text-lg px-8 py-6 gap-3">
              <MdPlayArrow className="h-5 w-5" />
              Start Practicing Now
            </Button>
            <Button variant="outline" size="lg" className="text-lg px-8 py-6">
              Watch Demo
            </Button>
          </div>

          {/* Social Proof */}
          <div className="flex flex-wrap justify-center items-center gap-8 text-muted-foreground">
            <div className="flex items-center gap-2">
              <MdStar className="text-yellow-500" />
              <span className="text-sm">4.9/5 rating</span>
            </div>
            <div className="flex items-center gap-2">
              <MdTrendingUp className="text-green-500" />
              <span className="text-sm">10k+ interviews conducted</span>
            </div>
            <div className="flex items-center gap-2">
              <MdCheckCircle className="text-blue-500" />
              <span className="text-sm">95% success rate</span>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              Why Choose BlueGen?
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Experience the most realistic interview practice with cutting-edge AI technology
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <Card className="border-0 shadow-lg">
              <CardContent className="p-8 text-center">
                                 <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                   <MdMic className="h-8 w-8 text-primary" />
                 </div>
                <h3 className="text-xl font-semibold mb-3">Real-time Voice Conversation</h3>
                <p className="text-muted-foreground">
                  Practice with natural voice interactions just like real interviews
                </p>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-lg">
              <CardContent className="p-8 text-center">
                <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <MdBusiness className="h-8 w-8 text-primary" />
                </div>
                <h3 className="text-xl font-semibold mb-3">Company-Specific Formats</h3>
                <p className="text-muted-foreground">
                  Practice interviews tailored to Google, Microsoft, Amazon, and more
                </p>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-lg">
              <CardContent className="p-8 text-center">
                <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <MdFeedback className="h-8 w-8 text-primary" />
                </div>
                <h3 className="text-xl font-semibold mb-3">Instant Feedback</h3>
                <p className="text-muted-foreground">
                  Get detailed feedback and improvement suggestions after each session
                </p>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-lg">
              <CardContent className="p-8 text-center">
                <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <MdSpeed className="h-8 w-8 text-primary" />
                </div>
                <h3 className="text-xl font-semibold mb-3">Adaptive Difficulty</h3>
                <p className="text-muted-foreground">
                  AI adjusts question difficulty based on your performance level
                </p>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-lg">
              <CardContent className="p-8 text-center">
                <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <MdCode className="h-8 w-8 text-primary" />
                </div>
                <h3 className="text-xl font-semibold mb-3">Technical & Behavioral</h3>
                <p className="text-muted-foreground">
                  Practice both coding challenges and behavioral questions
                </p>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-lg">
              <CardContent className="p-8 text-center">
                <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <MdLightbulb className="h-8 w-8 text-primary" />
                </div>
                <h3 className="text-xl font-semibold mb-3">Smart Analytics</h3>
                <p className="text-muted-foreground">
                  Track your progress and identify areas for improvement
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* How it Works Section */}
      <section id="how-it-works" className="py-20 px-4 bg-muted/30">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              How It Works
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Get started in just three simple steps
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-20 h-20 bg-primary rounded-full flex items-center justify-center mx-auto mb-6 text-primary-foreground text-2xl font-bold">
                1
              </div>
              <h3 className="text-xl font-semibold mb-3">Choose Your Interview Type</h3>
              <p className="text-muted-foreground">
                Select from various interview formats including technical, behavioral, or company-specific styles
              </p>
            </div>

            <div className="text-center">
              <div className="w-20 h-20 bg-primary rounded-full flex items-center justify-center mx-auto mb-6 text-primary-foreground text-2xl font-bold">
                2
              </div>
              <h3 className="text-xl font-semibold mb-3">Start the Conversation</h3>
              <p className="text-muted-foreground">
                Engage in a natural voice conversation with our AI interviewer using your microphone
              </p>
            </div>

            <div className="text-center">
              <div className="w-20 h-20 bg-primary rounded-full flex items-center justify-center mx-auto mb-6 text-primary-foreground text-2xl font-bold">
                3
              </div>
              <h3 className="text-xl font-semibold mb-3">Get Feedback & Improve</h3>
              <p className="text-muted-foreground">
                Receive detailed feedback and actionable insights to improve your interview skills
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Interview Modes Section */}
      <section id="interview-modes" className="py-20 px-4">
        <div className="container mx-auto max-w-4xl">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              Choose Your Interview Mode
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Practice with AI interviewers from top tech companies
            </p>
          </div>

          <Card className="mb-8 border-0 shadow-xl">
            <CardContent className="p-8 space-y-6">
              <Select value={selectedPrompt} onValueChange={setSelectedPrompt}>
                <SelectTrigger className="w-full h-14 text-lg">
                  <SelectValue placeholder="Select an interview mode..." />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(prompts).map(([key, prompt]) => (
                    <SelectItem key={key} value={key}>
                      <div className="flex items-center gap-3 py-2">
                        {iconMap[key]}
                        <div>
                          <div className="font-medium">{prompt.name}</div>
                          <div className="text-sm text-muted-foreground">{prompt.description}</div>
                        </div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {selectedPromptData && (
                <Card className="border border-primary/20 bg-primary/5">
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
                className="w-full h-14 text-lg gap-3"
                disabled={!selectedPrompt}
                onClick={handleStartInterview}
              >
                <MdPlayArrow className="h-5 w-5" />
                Start Interview
              </Button>
            </CardContent>
          </Card>

          {/* Tips Card */}
          <Card className="border-0 shadow-lg">
            <CardContent className="p-8">
              <div className="flex items-center gap-3 mb-4">
                <MdLightbulb className="text-primary text-2xl" />
                <h3 className="text-xl font-semibold text-foreground">Tips for Best Experience</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center gap-3">
                  <MdCheckCircle className="text-green-500 flex-shrink-0" />
                  <span className="text-muted-foreground">Use headphones to prevent audio feedback</span>
                </div>
                <div className="flex items-center gap-3">
                  <MdCheckCircle className="text-green-500 flex-shrink-0" />
                  <span className="text-muted-foreground">Ensure a quiet environment</span>
                </div>
                <div className="flex items-center gap-3">
                  <MdCheckCircle className="text-green-500 flex-shrink-0" />
                  <span className="text-muted-foreground">Allow microphone access when prompted</span>
                </div>
                <div className="flex items-center gap-3">
                  <MdCheckCircle className="text-green-500 flex-shrink-0" />
                  <span className="text-muted-foreground">Have a stable internet connection</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 border-t border-border/50">
        <div className="container mx-auto max-w-6xl text-center">
          <div className="flex items-center justify-center gap-2 mb-4">
            <MdMic className="text-2xl text-primary" />
            <span className="text-2xl font-bold">BlueGen</span>
          </div>
          <p className="text-muted-foreground">
            Practice. Improve. Succeed. Your next great opportunity starts here.
          </p>
        </div>
      </footer>
    </div>
  )
} 