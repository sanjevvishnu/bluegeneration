'use client'

import React from 'react'
import './globals.css'
import { ThemeProvider as NextThemesProvider } from 'next-themes'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <title>AI Interview Practice</title>
        <meta name="description" content="Practice technical interviews with AI-powered interviewers" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body>
        <NextThemesProvider attribute="class" defaultTheme="dark">
          {children}
        </NextThemesProvider>
      </body>
    </html>
  )
} 