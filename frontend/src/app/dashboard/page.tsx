'use client'

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
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
  MessageCircle
} from "lucide-react"
import Link from "next/link"
import { UserButton, useUser } from "@clerk/nextjs"
import { useEffect, useState } from "react"

export default function Dashboard() {
  const { user, isLoaded } = useUser()
  const [isUserSynced, setIsUserSynced] = useState(false)

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

  // Mock data - this would come from API/Supabase in real implementation
  const userStats = {
    totalInterviews: 12,
    completedInterviews: 10,
    averageScore: 8.5,
    currentStreak: 5,
    subscription: 'premium'
  }

  const recentInterviews = [
    {
      id: 1,
      title: "Amazon Technical Interview",
      date: "2024-01-15",
      duration: "25 mins",
      score: 8.7,
      status: "completed"
    },
    {
      id: 2,
      title: "Google System Design",
      date: "2024-01-12",
      duration: "30 mins", 
      score: 9.2,
      status: "completed"
    },
    {
      id: 3,
      title: "Microsoft Behavioral",
      date: "2024-01-10",
      duration: "20 mins",
      score: 8.1,
      status: "completed"
    }
  ]

  const interviewTypes = [
    {
      id: "amazon_interviewer",
      name: "Amazon Interview",
      description: "Technical + Leadership Principles",
      icon: "🚀",
      difficulty: "Medium"
    },
    {
      id: "google_interviewer", 
      name: "Google Interview",
      description: "Algorithms & System Design",
      icon: "🎯",
      difficulty: "Hard"
    },
    {
      id: "technical_screening",
      name: "Technical Screening",
      description: "General Programming Questions",
      icon: "💻",
      difficulty: "Easy"
    },
    {
      id: "behavioral",
      name: "Behavioral Interview",
      description: "Soft Skills & Experience",
      icon: "🤝",
      difficulty: "Easy"
    }
  ]

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="border-b border-border bg-card sticky top-0 z-50">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <Mic className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold text-foreground">Coimbatore</span>
          </Link>
          <div className="flex items-center space-x-4">
            <Link href="/transcripts">
              <Button variant="ghost" size="sm">
                <MessageCircle className="w-4 h-4 mr-2" />
                Transcripts
              </Button>
            </Link>
            <Button variant="ghost" size="sm">
              <Settings className="w-4 h-4 mr-2" />
              Settings
            </Button>
            <UserButton 
              appearance={{
                elements: {
                  avatarBox: "w-8 h-8"
                }
              }}
            />
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">
            Welcome back, {user?.firstName || 'there'}! 👋
          </h1>
          <p className="text-muted-foreground">
            Ready to practice your next interview? Let's help you land that dream job.
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Interviews</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{userStats.totalInterviews}</div>
              <p className="text-xs text-muted-foreground">
                +2 from last month
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Average Score</CardTitle>
              <Award className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{userStats.averageScore}/10</div>
              <p className="text-xs text-muted-foreground">
                +0.3 improvement
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Current Streak</CardTitle>
              <Target className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{userStats.currentStreak} days</div>
              <p className="text-xs text-muted-foreground">
                Keep it going!
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Subscription</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold capitalize">{userStats.subscription}</div>
              <p className="text-xs text-muted-foreground">
                Unlimited access
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Quick Start */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Play className="w-5 h-5" />
                  <span>Quick Start Interview</span>
                </CardTitle>
                <CardDescription>
                  Choose an interview type and start practicing immediately
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-2 gap-4">
                  {interviewTypes.map((type) => (
                    <Card key={type.id} className="border hover:border-primary/50 transition-colors cursor-pointer">
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between mb-3">
                          <div className="text-2xl">{type.icon}</div>
                          <Badge variant={type.difficulty === 'Easy' ? 'secondary' : type.difficulty === 'Medium' ? 'default' : 'destructive'}>
                            {type.difficulty}
                          </Badge>
                        </div>
                        <h3 className="font-semibold mb-2">{type.name}</h3>
                        <p className="text-sm text-muted-foreground mb-4">{type.description}</p>
                        <Link href="/interview">
                          <Button size="sm" className="w-full">
                            Start Interview
                          </Button>
                        </Link>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Recent Interviews */}
            <Card className="mt-6">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Clock className="w-5 h-5" />
                  <span>Recent Interviews</span>
                </CardTitle>
                <CardDescription>
                  Review your past interview performance
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recentInterviews.map((interview) => (
                    <div key={interview.id} className="flex items-center justify-between p-4 border border-border rounded-lg hover:bg-muted/50 transition-colors">
                      <div className="flex-1">
                        <h4 className="font-medium">{interview.title}</h4>
                        <div className="flex items-center space-x-4 text-sm text-muted-foreground mt-1">
                          <span>{interview.date}</span>
                          <span>{interview.duration}</span>
                        </div>
                      </div>
                      <div className="flex items-center space-x-4">
                        <div className="text-right">
                          <div className="font-semibold text-green-600">
                            {interview.score}/10
                          </div>
                          <Badge variant="secondary" className="text-xs">
                            {interview.status}
                          </Badge>
                        </div>
                        <Button variant="ghost" size="sm">
                          View Details
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
                <Separator className="my-4" />
                <Button variant="outline" className="w-full">
                  View All Interviews
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Progress Overview */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <TrendingUp className="w-5 h-5" />
                  <span>Your Progress</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Interview Completion</span>
                    <span>83%</span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2">
                    <div className="bg-primary h-2 rounded-full" style={{ width: '83%' }}></div>
                  </div>
                </div>
                
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Technical Skills</span>
                    <span>8.5/10</span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2">
                    <div className="bg-chart-2 h-2 rounded-full" style={{ width: '85%' }}></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Communication</span>
                    <span>7.8/10</span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2">
                    <div className="bg-chart-3 h-2 rounded-full" style={{ width: '78%' }}></div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Learning Resources */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <BookOpen className="w-5 h-5" />
                  <span>Learning Resources</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button variant="outline" size="sm" className="w-full justify-start">
                  <Calendar className="w-4 h-4 mr-2" />
                  Schedule Practice
                </Button>
                <Button variant="outline" size="sm" className="w-full justify-start">
                  <Target className="w-4 h-4 mr-2" />
                  Skill Assessment
                </Button>
                <Button variant="outline" size="sm" className="w-full justify-start">
                  <BookOpen className="w-4 h-4 mr-2" />
                  Study Guides
                </Button>
              </CardContent>
            </Card>

            {/* Upcoming Features */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">🚀 Coming Soon</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm text-muted-foreground">
                  <p>• Mock interviews with real engineers</p>
                  <p>• Industry-specific practice tracks</p>
                  <p>• Advanced performance analytics</p>
                  <p>• Interview scheduling assistant</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
} 