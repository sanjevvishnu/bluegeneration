'use client'

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { FontToggleButton } from "@/components/ui/font-toggle-button"
import { 
  Play,
  Clock,
  TrendingUp,
  Calendar,
  BookOpen,
  Settings,
  LogOut,
  Mic,
  BarChart3,
  Target,
  Award,
  MessageCircle,
  User,
  Home,
  FileText,
  HelpCircle,
  Bell,
  Search,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Copy,
  Download,
  AlertCircle,
  Bot
} from "lucide-react"
import Link from "next/link"
import { UserButton, useUser } from "@clerk/nextjs"
import { useEffect, useState } from "react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription } from "@/components/ui/alert"

// Types for API responses
interface UserStats {
  total_interviews: number
  completed_interviews: number
  average_score: number
  current_streak: number
  subscription_tier: string
  interviews_used_this_month: number
}

interface RecentInterview {
  id: string
  session_id: string
  mode: string
  status: string
  title: string | null
  duration: number | null
  performance_score: number | null
  difficulty_level: string
  created_at: string
  completed_at: string | null
}

interface TranscriptEntry {
  id: string
  speaker: 'user' | 'assistant'
  text: string
  created_at: string
  provider?: string
  confidence_score?: number
}

export default function Dashboard() {
  const { user, isLoaded } = useUser()
  const [isUserSynced, setIsUserSynced] = useState(false)
  const [userStats, setUserStats] = useState<UserStats | null>(null)
  const [recentInterviews, setRecentInterviews] = useState<RecentInterview[]>([])
  const [isLoadingStats, setIsLoadingStats] = useState(true)
  const [isLoadingInterviews, setIsLoadingInterviews] = useState(true)
  const [showRecentInterviews, setShowRecentInterviews] = useState(false)
  const [activeTab, setActiveTab] = useState('dashboard')
  
  // Transcript state
  const [sessionId, setSessionId] = useState('')
  const [transcripts, setTranscripts] = useState<TranscriptEntry[]>([])
  const [transcriptLoading, setTranscriptLoading] = useState(false)
  const [transcriptError, setTranscriptError] = useState<string | null>(null)
  const [recentSessions, setRecentSessions] = useState<RecentInterview[]>([])
  const [loadingRecentSessions, setLoadingRecentSessions] = useState(false)

  // Auto-sync user to Supabase on first visit
  useEffect(() => {
    const syncUserToSupabase = async () => {
      if (!isLoaded || !user || isUserSynced) return

      try {
        console.log('🔄 Syncing user to Supabase:', user.id)
        
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/user/create-user`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            id: user.id,
            email_addresses: user.emailAddresses.map(email => ({
              email_address: email.emailAddress,
              primary: email.id === user.primaryEmailAddressId
            })),
            first_name: user.firstName,
            last_name: user.lastName
          })
        })

        if (response.ok) {
          const result = await response.json()
          console.log('✅ User synced to Supabase:', result)
          setIsUserSynced(true)
        } else {
          // User might already exist, which is fine
          console.log('ℹ️ User sync response:', response.status)
          setIsUserSynced(true)
        }
      } catch (error) {
        console.error('❌ Error syncing user:', error)
      }
    }

    syncUserToSupabase()
  }, [isLoaded, user, isUserSynced])

  // Fetch user statistics
  useEffect(() => {
    const fetchUserStats = async () => {
      if (!isLoaded || !user) return

      try {
        setIsLoadingStats(true)
        console.log('📊 Fetching user stats for:', user.id)
        
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/user/stats`, {
          headers: {
            'Authorization': `Bearer ${user.id}`,
            'Content-Type': 'application/json',
          },
        })

        if (response.ok) {
          const stats = await response.json()
          console.log('✅ User stats fetched:', stats)
          setUserStats(stats)
        } else {
          console.error('❌ Failed to fetch user stats:', response.status)
          // Set default stats if API fails
          setUserStats({
            total_interviews: 0,
            completed_interviews: 0,
            average_score: 0,
            current_streak: 0,
            subscription_tier: 'free',
            interviews_used_this_month: 0
          })
        }
      } catch (error) {
        console.error('❌ Error fetching user stats:', error)
        // Set default stats if API fails
        setUserStats({
          total_interviews: 0,
          completed_interviews: 0,
          average_score: 0,
          current_streak: 0,
          subscription_tier: 'free',
          interviews_used_this_month: 0
        })
      } finally {
        setIsLoadingStats(false)
      }
    }

    fetchUserStats()
  }, [isLoaded, user, isUserSynced])

  // Fetch recent interviews
  useEffect(() => {
    const fetchRecentInterviews = async () => {
      if (!isLoaded || !user) return

      try {
        setIsLoadingInterviews(true)
        console.log('📝 Fetching recent interviews for:', user.id)
        
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/user/conversations?limit=5`, {
          headers: {
            'Authorization': `Bearer ${user.id}`,
            'Content-Type': 'application/json',
          },
        })

        if (response.ok) {
          const interviews = await response.json()
          console.log('✅ Recent interviews fetched:', interviews)
          setRecentInterviews(interviews)
        } else {
          console.error('❌ Failed to fetch recent interviews:', response.status)
          setRecentInterviews([])
        }
      } catch (error) {
        console.error('❌ Error fetching recent interviews:', error)
        setRecentInterviews([])
      } finally {
        setIsLoadingInterviews(false)
      }
    }

    fetchRecentInterviews()
  }, [isLoaded, user, isUserSynced])

  // Helper function to format date
  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString()
    } catch {
      return dateString
    }
  }

  // Helper function to format duration
  const formatDuration = (duration: number | null) => {
    if (!duration) return 'N/A'
    const minutes = Math.floor(duration / 60)
    const seconds = duration % 60
    return `${minutes}:${seconds.toString().padStart(2, '0')}`
  }

  const fetchTranscripts = async () => {
    if (!sessionId.trim()) {
      setTranscriptError('Please enter a session ID')
      return
    }

    setTranscriptLoading(true)
    setTranscriptError(null)

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/transcripts/${sessionId}?format=conversation`)
      
      if (!response.ok) {
        if (response.status === 404) {
          setTranscriptError('Session not found. Please check the session ID.')
        } else {
          setTranscriptError('Failed to fetch transcripts')
        }
        setTranscripts([])
        return
      }

      const data = await response.json()
      // Handle the API response format: {format: "conversation", content: [...]}
      const transcriptArray = data.content || data
      setTranscripts(transcriptArray)
    } catch (error) {
      setTranscriptError('Error fetching transcripts')
      setTranscripts([])
    } finally {
      setTranscriptLoading(false)
    }
  }

  const copyTranscript = () => {
    const transcriptText = transcripts
      .map(entry => `${entry.speaker.toUpperCase()}: ${entry.text}`)
      .join('\n')
    
    navigator.clipboard.writeText(transcriptText)
  }

  const downloadTranscript = () => {
    const transcriptText = transcripts
      .map(entry => `${entry.speaker.toUpperCase()}: ${entry.text}`)
      .join('\n')
    
    const blob = new Blob([transcriptText], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `transcript-${sessionId}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const fetchRecentSessions = async () => {
    if (!isLoaded || !user) return

    setLoadingRecentSessions(true)
    try {
      console.log('📋 Fetching recent sessions for transcripts for:', user.id)
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/user/conversations?limit=10`, {
        headers: {
          'Authorization': `Bearer ${user.id}`,
          'Content-Type': 'application/json',
        },
      })

      if (response.ok) {
        const sessions = await response.json()
        console.log('✅ Recent sessions fetched:', sessions)
        setRecentSessions(sessions)
      } else {
        console.error('❌ Failed to fetch recent sessions:', response.status)
        setRecentSessions([])
      }
    } catch (error) {
      console.error('❌ Error fetching recent sessions:', error)
      setRecentSessions([])
    } finally {
      setLoadingRecentSessions(false)
    }
  }

  // Fetch recent sessions when switching to transcripts tab
  useEffect(() => {
    if (activeTab === 'transcripts') {
      fetchRecentSessions()
    }
  }, [activeTab, isLoaded, user])

  const interviewTypes = [
    {
      id: "amazon_interviewer",
      name: "Amazon Interview",
      description: "Technical + Leadership Principles",
      icon: "🚀",
      difficulty: "Medium",
      color: "bg-background border-border hover:bg-secondary hover:border-accent transition-all duration-200"
    },
    {
      id: "google_interviewer", 
      name: "Google Interview",
      description: "Algorithms & System Design",
      icon: "🎯",
      difficulty: "Hard",
      color: "bg-background border-border hover:bg-secondary hover:border-accent transition-all duration-200"
    },
    {
      id: "technical_screening",
      name: "Technical Screening",
      description: "General Programming Questions",
      icon: "💻",
      difficulty: "Easy",
      color: "bg-background border-border hover:bg-secondary hover:border-accent transition-all duration-200"
    },
    {
      id: "behavioral",
      name: "Behavioral Interview",
      description: "Soft Skills & Experience",
      icon: "🤝",
      difficulty: "Easy",
      color: "bg-background border-border hover:bg-secondary hover:border-accent transition-all duration-200"
    }
  ]

  const sidebarItems = [
    { name: 'Dashboard', icon: Home, tab: 'dashboard' },
    { name: 'Interviews', icon: Mic, href: '/interview' },
    { name: 'Transcripts', icon: FileText, tab: 'transcripts' },
    { name: 'Analytics', icon: BarChart3, href: '/analytics' },
    { name: 'Resources', icon: BookOpen, href: '/resources' },
    { name: 'Help', icon: HelpCircle, href: '/help' },
  ]

  return (
    <div className="h-screen bg-gradient-to-br from-neutral-50 via-white to-neutral-100 flex overflow-hidden">
      {/* Sidebar */}
      <div className="w-64 bg-sidebar-background border-r border-sidebar-border flex flex-col">
        {/* Logo */}
        <div className="p-4">
          <Link href="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <Mic className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold text-sidebar-foreground">Coimbatore</span>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-3">
          <ul className="space-y-1">
            {sidebarItems.map((item) => (
              <li key={item.name}>
                {item.href ? (
                  <Link href={item.href}>
                    <div className="flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground">
                      <item.icon className="w-4 h-4" />
                      <span className="font-medium text-sm">{item.name}</span>
                    </div>
                  </Link>
                ) : (
                  <button
                    onClick={() => setActiveTab(item.tab!)}
                    className={`flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors w-full text-left ${
                      activeTab === item.tab
                        ? 'bg-accent text-accent-foreground' 
                        : 'text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground'
                    }`}
                  >
                    <item.icon className="w-4 h-4" />
                    <span className="font-medium text-sm">{item.name}</span>
                  </button>
                )}
              </li>
            ))}
          </ul>
        </nav>

        {/* User Section */}
        <div className="p-3 border-t border-sidebar-border">
          <div className="flex items-center space-x-3 mb-3">
            <UserButton 
              appearance={{
                elements: {
                  avatarBox: "w-8 h-8",
                  userButtonPopoverCard: "bg-background border-border",
                  userButtonPopoverText: "text-foreground"
                }
              }}
            />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-sidebar-foreground truncate">
                {user?.firstName || 'User'}
              </p>
              <p className="text-xs text-muted-foreground truncate">
                {userStats?.subscription_tier || 'free'} plan
              </p>
            </div>
          </div>
          <div className="space-y-1">
            <Button variant="ghost" size="sm" className="w-full justify-start text-sidebar-foreground hover:bg-sidebar-accent text-xs py-1 h-7">
              <Settings className="w-3 h-3 mr-2" />
              Settings
            </Button>
            <FontToggleButton />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <header className="bg-white/80 backdrop-blur-sm border-b border-border px-4 py-3">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-foreground">
                Welcome back, {user?.firstName || 'there'}! 👋
              </h1>
              <p className="text-sm text-muted-foreground">
                Ready to practice your next interview? Let's help you land that dream job.
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
                <Search className="w-4 h-4" />
              </Button>
              <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
                <Bell className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </header>

        {/* Content Area */}
        <div className="flex-1 overflow-auto p-4">
          {activeTab === 'dashboard' && (
            <div>
              {/* Stats Cards */}
          <div className="grid grid-cols-4 gap-4 mb-4">
            <Card className="border-border bg-background">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-foreground">Total Interviews</CardTitle>
                <div className="w-6 h-6 bg-accent/10 rounded-lg flex items-center justify-center">
                  <BarChart3 className="h-3 w-3 text-accent" />
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="text-xl font-bold text-foreground">
                  {isLoadingStats ? '...' : userStats?.total_interviews || 0}
                </div>
                <p className="text-xs text-muted-foreground">
                  {userStats?.total_interviews ? '+2 from last month' : 'Start your first interview!'}
                </p>
              </CardContent>
            </Card>

            <Card className="border-border bg-background">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-foreground">Average Score</CardTitle>
                <div className="w-6 h-6 bg-accent/10 rounded-lg flex items-center justify-center">
                  <Award className="h-3 w-3 text-accent" />
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="text-xl font-bold text-foreground">
                  {isLoadingStats ? '...' : userStats?.average_score ? `${userStats.average_score.toFixed(1)}/10` : '0/10'}
                </div>
                <p className="text-xs text-muted-foreground">
                  {userStats?.average_score ? '+0.3 improvement' : 'Complete interviews to see your score'}
                </p>
              </CardContent>
            </Card>

            <Card className="border-border bg-background">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-foreground">Current Streak</CardTitle>
                <div className="w-6 h-6 bg-accent/10 rounded-lg flex items-center justify-center">
                  <Target className="h-3 w-3 text-accent" />
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="text-xl font-bold text-foreground">
                  {isLoadingStats ? '...' : `${userStats?.current_streak || 0} days`}
                </div>
                <p className="text-xs text-muted-foreground">
                  {userStats?.current_streak ? 'Keep it going!' : 'Start your streak today!'}
                </p>
              </CardContent>
            </Card>

            <Card className="border-border bg-background">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-foreground">Subscription</CardTitle>
                <div className="w-6 h-6 bg-accent/10 rounded-lg flex items-center justify-center">
                  <TrendingUp className="h-3 w-3 text-accent" />
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="text-xl font-bold capitalize text-foreground">
                  {isLoadingStats ? '...' : userStats?.subscription_tier || 'free'}
                </div>
                <p className="text-xs text-muted-foreground">
                  {userStats?.subscription_tier === 'premium' ? 'Unlimited access' : `${userStats?.interviews_used_this_month || 0}/3 interviews used`}
                </p>
              </CardContent>
            </Card>
          </div>

          <div className="grid lg:grid-cols-3 gap-4 h-full">
            {/* Quick Start */}
            <div className="lg:col-span-2 flex flex-col">
              <Card className="border-border bg-background flex-1">
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center space-x-2 text-foreground text-lg">
                    <div className="w-5 h-5 bg-accent/10 rounded-md flex items-center justify-center">
                      <Play className="w-3 h-3 text-accent" />
                    </div>
                    <span>Quick Start Interview</span>
                  </CardTitle>
                  <CardDescription className="text-muted-foreground text-sm">
                    Choose an interview type and start practicing immediately
                  </CardDescription>
                </CardHeader>
                <CardContent className="flex-1">
                  <div className="grid md:grid-cols-2 gap-3 mb-4">
                    {interviewTypes.map((type) => (
                      <Card key={type.id} className={`${type.color} cursor-pointer group`}>
                        <CardContent className="p-3">
                          <div className="flex items-start justify-between mb-2">
                            <div className="text-xl">{type.icon}</div>
                            <Badge variant={type.difficulty === 'Easy' ? 'secondary' : type.difficulty === 'Medium' ? 'default' : 'destructive'} className="text-xs">
                              {type.difficulty}
                            </Badge>
                          </div>
                          <h3 className="font-semibold mb-1 text-foreground text-sm">{type.name}</h3>
                          <p className="text-xs text-muted-foreground mb-3">{type.description}</p>
                          <Link href="/interview">
                            <Button size="sm" className="w-full bg-primary hover:bg-primary/90 text-primary-foreground text-xs">
                              Start Interview
                            </Button>
                          </Link>
                        </CardContent>
                      </Card>
                    ))}
                  </div>

                  {/* Toggleable Recent Interviews */}
                  <div className="border-t border-border pt-3">
                    <Button 
                      variant="ghost" 
                      onClick={() => setShowRecentInterviews(!showRecentInterviews)}
                      className="w-full justify-between p-0 h-auto font-medium text-foreground hover:bg-transparent"
                    >
                      <div className="flex items-center space-x-2">
                        <Clock className="w-4 h-4 text-accent" />
                        <span className="text-sm">Recent Interviews ({recentInterviews.length})</span>
                      </div>
                      {showRecentInterviews ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </Button>
                    
                    {showRecentInterviews && (
                      <div className="mt-3 space-y-2 max-h-48 overflow-y-auto">
                        {isLoadingInterviews ? (
                          <div className="space-y-2">
                            {[1, 2].map((i) => (
                              <div key={i} className="flex items-center justify-between p-2 border border-border rounded-lg bg-background">
                                <div className="flex-1">
                                  <div className="h-3 bg-muted rounded w-32 mb-1"></div>
                                  <div className="h-2 bg-muted rounded w-24"></div>
                                </div>
                                <div className="h-3 bg-muted rounded w-12"></div>
                              </div>
                            ))}
                          </div>
                        ) : recentInterviews.length > 0 ? (
                          <div className="space-y-2">
                            {recentInterviews.slice(0, 3).map((interview) => (
                              <div key={interview.id} className="flex items-center justify-between p-2 border border-border rounded-lg hover:bg-secondary transition-colors bg-background">
                                <div className="flex-1">
                                  <h4 className="font-medium text-foreground text-sm">{interview.title || `${interview.mode} Interview`}</h4>
                                  <div className="flex items-center space-x-3 text-xs text-muted-foreground">
                                    <span>{formatDate(interview.created_at)}</span>
                                    <span>{formatDuration(interview.duration)}</span>
                                  </div>
                                </div>
                                <div className="text-right">
                                  <div className="font-semibold text-foreground text-sm">
                                    {interview.performance_score ? `${interview.performance_score.toFixed(1)}/10` : 'N/A'}
                                  </div>
                                  <Badge variant="secondary" className="text-xs">
                                    {interview.status}
                                  </Badge>
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="text-center py-4">
                            <MessageCircle className="w-8 h-8 text-accent mx-auto mb-2" />
                            <p className="text-foreground font-medium text-sm">No interviews yet</p>
                            <p className="text-xs text-muted-foreground">Start your first interview to see your history here</p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Sidebar */}
            <div className="space-y-4 flex flex-col">
              {/* Progress Overview */}
              <Card className="border-border bg-background">
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center space-x-2 text-foreground text-base">
                    <div className="w-5 h-5 bg-accent/10 rounded-md flex items-center justify-center">
                      <TrendingUp className="w-3 h-3 text-accent" />
                    </div>
                    <span>Your Progress</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <div className="flex justify-between text-xs mb-1 text-foreground">
                      <span>Interview Completion</span>
                      <span className="text-accent font-medium">{userStats?.total_interviews ? Math.min(100, (userStats.completed_interviews / userStats.total_interviews) * 100).toFixed(0) : 0}%</span>
                    </div>
                    <div className="w-full bg-secondary rounded-full h-1.5">
                      <div 
                        className="bg-accent h-1.5 rounded-full transition-all duration-500" 
                        style={{ width: `${userStats?.total_interviews ? Math.min(100, (userStats.completed_interviews / userStats.total_interviews) * 100) : 0}%` }}
                      ></div>
                    </div>
                  </div>
                  
                  <div>
                    <div className="flex justify-between text-xs mb-1 text-foreground">
                      <span>Technical Skills</span>
                      <span className="text-accent font-medium">{userStats?.average_score ? `${userStats.average_score.toFixed(1)}/10` : '0/10'}</span>
                    </div>
                    <div className="w-full bg-secondary rounded-full h-1.5">
                      <div 
                        className="bg-accent h-1.5 rounded-full transition-all duration-500" 
                        style={{ width: `${userStats?.average_score ? (userStats.average_score / 10) * 100 : 0}%` }}
                      ></div>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-xs mb-1 text-foreground">
                      <span>Consistency</span>
                      <span className="text-accent font-medium">{userStats?.current_streak || 0} days</span>
                    </div>
                    <div className="w-full bg-secondary rounded-full h-1.5">
                      <div 
                        className="bg-accent h-1.5 rounded-full transition-all duration-500" 
                        style={{ width: `${Math.min(100, ((userStats?.current_streak || 0) / 30) * 100)}%` }}
                      ></div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Learning Resources */}
              <Card className="border-border bg-background">
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center space-x-2 text-foreground text-base">
                    <div className="w-5 h-5 bg-accent/10 rounded-md flex items-center justify-center">
                      <BookOpen className="w-3 h-3 text-accent" />
                    </div>
                    <span>Learning Resources</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <Button variant="outline" size="sm" className="w-full justify-start hover:border-accent hover:text-accent text-xs py-1 h-7">
                    <Calendar className="w-3 h-3 mr-2" />
                    Schedule Practice
                  </Button>
                  <Button variant="outline" size="sm" className="w-full justify-start hover:border-accent hover:text-accent text-xs py-1 h-7">
                    <Target className="w-3 h-3 mr-2" />
                    Skill Assessment
                  </Button>
                  <Button variant="outline" size="sm" className="w-full justify-start hover:border-accent hover:text-accent text-xs py-1 h-7">
                    <BookOpen className="w-3 h-3 mr-2" />
                    Study Guides
                  </Button>
                </CardContent>
              </Card>

              {/* Upcoming Features */}
              <Card className="border-border bg-background flex-1">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm text-foreground">🚀 Coming Soon</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-xs text-muted-foreground">
                    <div className="flex items-center space-x-2">
                      <div className="w-1.5 h-1.5 bg-accent rounded-full"></div>
                      <span>Mock interviews with real engineers</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-1.5 h-1.5 bg-accent rounded-full"></div>
                      <span>Industry-specific practice tracks</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-1.5 h-1.5 bg-accent rounded-full"></div>
                      <span>Advanced performance analytics</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-1.5 h-1.5 bg-accent rounded-full"></div>
                      <span>Interview scheduling assistant</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
            </div>
          )}

          {activeTab === 'transcripts' && (
            <div>
              {/* Header */}
              <div className="mb-8">
                <h2 className="text-3xl font-bold text-gray-800 mb-2">Interview Transcripts</h2>
                <p className="text-gray-600">View conversation transcripts from your interview sessions</p>
              </div>

              {/* Recent Sessions */}
              <Card className="mb-6">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Your Recent Sessions</CardTitle>
                      <CardDescription>Click on any session to load its transcript</CardDescription>
                    </div>
                    <Button variant="outline" size="sm" onClick={fetchRecentSessions} disabled={loadingRecentSessions}>
                      {loadingRecentSessions ? (
                        <>
                          <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                          Loading...
                        </>
                      ) : (
                        <>
                          <RefreshCw className="w-4 h-4 mr-2" />
                          Refresh
                        </>
                      )}
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {loadingRecentSessions ? (
                    <div className="space-y-2">
                      {[1, 2, 3].map((i) => (
                        <div key={i} className="flex items-center justify-between p-3 border border-border rounded-lg bg-background animate-pulse">
                          <div className="flex-1">
                            <div className="h-4 bg-muted rounded w-48 mb-2"></div>
                            <div className="h-3 bg-muted rounded w-32"></div>
                          </div>
                          <div className="h-8 bg-muted rounded w-20"></div>
                        </div>
                      ))}
                    </div>
                  ) : recentSessions.length > 0 ? (
                    <div className="space-y-2 max-h-64 overflow-y-auto">
                      {recentSessions.map((session) => (
                        <div
                          key={session.id}
                          className="flex items-center justify-between p-3 border border-border rounded-lg hover:bg-secondary transition-colors cursor-pointer"
                          onClick={() => {
                            setSessionId(session.session_id)
                            fetchTranscripts()
                          }}
                        >
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-1">
                              <h4 className="font-medium text-foreground text-sm">
                                {session.title || `${session.mode.replace('_', ' ')} Interview`}
                              </h4>
                              <Badge variant={session.status === 'completed' ? 'default' : session.status === 'active' ? 'secondary' : 'outline'} className="text-xs">
                                {session.status}
                              </Badge>
                            </div>
                            <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                              <span>📋 {session.session_id}</span>
                              <span>📅 {formatDate(session.created_at)}</span>
                              {session.duration && <span>⏱️ {formatDuration(session.duration)}</span>}
                              {session.performance_score && (
                                <span>🎯 {session.performance_score.toFixed(1)}/10</span>
                              )}
                            </div>
                          </div>
                          <Button size="sm" variant="ghost">
                            View Transcript
                          </Button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <MessageCircle className="w-12 h-12 text-muted-foreground mx-auto mb-4 opacity-50" />
                      <p className="text-muted-foreground font-medium">No interview sessions found</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        Start an interview to see your sessions here
                      </p>
                      <Link href="/interview">
                        <Button className="mt-4" size="sm">
                          <Mic className="w-4 h-4 mr-2" />
                          Start Interview
                        </Button>
                      </Link>
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Load Specific Transcript</CardTitle>
                  <CardDescription>Enter a session ID manually to view any conversation transcript</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex gap-4">
                    <div className="flex-1">
                      <Label htmlFor="sessionId">Session ID</Label>
                      <Input
                        id="sessionId"
                        placeholder="Enter session ID (e.g., session_123abc)"
                        value={sessionId}
                        onChange={(e) => setSessionId(e.target.value)}
                        className="mt-1"
                      />
                    </div>
                    <div className="flex items-end gap-2">
                      <Button onClick={fetchTranscripts} disabled={transcriptLoading || !sessionId.trim()}>
                        {transcriptLoading ? (
                          <>
                            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                            Loading...
                          </>
                        ) : (
                          'Load Transcript'
                        )}
                      </Button>
                      {sessionId && (
                        <Button variant="outline" onClick={() => setSessionId('')}>
                          Clear
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {transcriptError && (
                <Alert className="mb-6" variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{transcriptError}</AlertDescription>
                </Alert>
              )}

              {transcripts.length > 0 && (
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle>Conversation Transcript</CardTitle>
                        <CardDescription>Session ID: {sessionId}</CardDescription>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm" onClick={copyTranscript}>
                          <Copy className="w-4 h-4 mr-2" />
                          Copy
                        </Button>
                        <Button variant="outline" size="sm" onClick={downloadTranscript}>
                          <Download className="w-4 h-4 mr-2" />
                          Download
                        </Button>
                        <Button variant="outline" size="sm" onClick={fetchTranscripts}>
                          <RefreshCw className="w-4 h-4 mr-2" />
                          Refresh
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4 max-h-96 overflow-y-auto">
                      {transcripts.map((entry, index) => (
                        <div
                          key={`${entry.timestamp}-${index}`}
                          className={`flex gap-3 p-3 rounded-lg ${
                            entry.speaker === 'user' 
                              ? 'bg-blue-50 border-l-4 border-blue-400' 
                              : 'bg-gray-50 border-l-4 border-gray-400'
                          }`}
                        >
                          <div className="flex-shrink-0">
                            {entry.speaker === 'user' ? (
                              <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                                <Mic className="w-4 h-4 text-white" />
                              </div>
                            ) : (
                              <div className="w-8 h-8 bg-gray-500 rounded-full flex items-center justify-center">
                                <Bot className="w-4 h-4 text-white" />
                              </div>
                            )}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-medium capitalize">
                                {entry.speaker === 'user' ? 'You' : 'Assistant'}
                              </span>
                              <span className="text-xs text-gray-500">
                                {formatTime(entry.created_at)}
                              </span>
                            </div>
                            <p className="text-gray-700">{entry.text}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
