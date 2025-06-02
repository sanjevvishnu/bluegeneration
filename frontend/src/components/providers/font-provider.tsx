'use client'

import React, { createContext, useContext, useEffect, useState } from 'react'

type Font = 'satoshi' | 'dm-sans'

interface FontContextType {
  font: Font
  setFont: (font: Font) => void
}

const FontContext = createContext<FontContextType | undefined>(undefined)

export function FontProvider({ children }: { children: React.ReactNode }) {
  const [font, setFont] = useState<Font>('satoshi')

  useEffect(() => {
    // Load saved font preference from localStorage
    const savedFont = localStorage.getItem('preferred-font') as Font
    if (savedFont && (savedFont === 'satoshi' || savedFont === 'dm-sans')) {
      setFont(savedFont)
    }
  }, [])

  useEffect(() => {
    // Apply font to document
    document.documentElement.style.setProperty(
      '--font-family',
      font === 'satoshi' 
        ? 'Satoshi, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
        : '"DM Sans", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    )

    // Update body class
    document.body.className = document.body.className.replace(/font-(satoshi|dm-sans)/, '')
    document.body.classList.add(`font-${font}`)

    // Save to localStorage
    localStorage.setItem('preferred-font', font)
  }, [font])

  return (
    <FontContext.Provider value={{ font, setFont }}>
      {children}
    </FontContext.Provider>
  )
}

export function useFont() {
  const context = useContext(FontContext)
  if (context === undefined) {
    throw new Error('useFont must be used within a FontProvider')
  }
  return context
} 