'use client'

import { Type } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useFont } from '@/components/providers/font-provider'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

export function FontToggleButton() {
  const { font, setFont } = useFont()

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="sm" className="gap-2">
          <Type className="h-4 w-4" />
          <span className="hidden sm:inline">
            {font === 'satoshi' ? 'Satoshi' : 'DM Sans'}
          </span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem
          onClick={() => setFont('satoshi')}
          className={font === 'satoshi' ? 'bg-accent' : ''}
        >
          <span className="font-satoshi">Satoshi</span>
          {font === 'satoshi' && <span className="ml-auto">✓</span>}
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => setFont('dm-sans')}
          className={font === 'dm-sans' ? 'bg-accent' : ''}
        >
          <span className="font-dm-sans">DM Sans</span>
          {font === 'dm-sans' && <span className="ml-auto">✓</span>}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
} 