'use client'

import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { useTheme } from 'next-themes'
import { MdLightMode, MdDarkMode, MdMic, MdPlayArrow, MdInfo, MdBusinessCenter } from 'react-icons/md'
import { cn } from '@/lib/utils'

interface FloatingNavbarProps {
  onStartInterview?: () => void
  hasInterviewSelected?: boolean
}

export default function FloatingNavbar({ onStartInterview, hasInterviewSelected }: FloatingNavbarProps) {
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20)
    }

    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark')
  }

  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' })
    }
  }

  return (
    <nav className={cn(
      "fixed top-4 left-1/2 transform -translate-x-1/2 z-50 transition-all duration-300",
      "bg-background/80 backdrop-blur-md border border-border/50 rounded-full px-6 py-3",
      "shadow-lg shadow-black/5",
      scrolled ? "bg-background/95" : "bg-background/80"
    )}>
      <div className="flex items-center gap-6">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <div className="relative">
            <MdMic className="text-xl text-primary" />
            <div className="absolute -inset-1 bg-primary/20 rounded-full blur-sm -z-10"></div>
          </div>
          <span className="font-bold text-lg">BlueGen</span>
        </div>

        {/* Navigation Links */}
        <div className="hidden md:flex items-center gap-4">
          <Button 
            variant="ghost" 
            size="sm"
            onClick={() => scrollToSection('features')}
            className="text-muted-foreground hover:text-foreground"
          >
            Features
          </Button>
          <Button 
            variant="ghost" 
            size="sm"
            onClick={() => scrollToSection('how-it-works')}
            className="text-muted-foreground hover:text-foreground"
          >
            How it Works
          </Button>
          <Button 
            variant="ghost" 
            size="sm"
            onClick={() => scrollToSection('interview-modes')}
            className="text-muted-foreground hover:text-foreground"
          >
            Interview Modes
          </Button>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3">
          {mounted && (
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleTheme}
              className="w-9 h-9"
            >
              {theme === 'dark' ? 
                <MdLightMode className="h-4 w-4" /> : 
                <MdDarkMode className="h-4 w-4" />
              }
            </Button>
          )}
          
          {hasInterviewSelected && onStartInterview && (
            <Button 
              onClick={onStartInterview}
              size="sm"
              className="gap-2"
            >
              <MdPlayArrow className="h-4 w-4" />
              Start Interview
            </Button>
          )}
        </div>
      </div>
    </nav>
  )
} 