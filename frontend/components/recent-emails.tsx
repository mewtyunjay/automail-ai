"use client"

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { useEffect, useState } from "react"
import { Skeleton } from "@/components/ui/skeleton"

interface EmailTime {
  relative: string
  time: string
  date: string
  full: string
  timestamp: string
}

interface Email {
  id: string
  senderName: string
  senderInitials: string
  subject: string
  preview: string
  time: EmailTime
  avatarUrl: string | null
}

export function RecentEmails() {
  const [emails, setEmails] = useState<Email[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [retryCount, setRetryCount] = useState(0)

  useEffect(() => {
    const fetchRecentEmails = async () => {
      try {
        setLoading(true)
        const response = await fetch('http://localhost:8000/recent-emails')
        
        if (!response.ok) {
          const errorText = await response.text().catch(() => 'Unknown error');
          throw new Error(`Error fetching emails (${response.status}): ${errorText}`)
        }
        
        const data = await response.json()
        setEmails(data.emails)
        setError(null)
      } catch (err) {
        console.error('Failed to fetch recent emails:', err)
        setError(`Failed to load recent emails: ${err instanceof Error ? err.message : 'Unknown error'}`)
      } finally {
        setLoading(false)
      }
    }

    fetchRecentEmails()
  }, [retryCount])

  if (loading) {
    return (
      <div className="space-y-8">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="flex items-center">
            <Skeleton className="h-9 w-9 rounded-full" />
            <div className="ml-4 space-y-1 flex-1">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-3 w-40" />
            </div>
            <Skeleton className="h-4 w-12 ml-auto" />
          </div>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 text-center">
        <p className="text-red-500 mb-3">{error}</p>
        <button 
          onClick={() => setRetryCount(prev => prev + 1)}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
        >
          Retry
        </button>
      </div>
    )
  }

  if (emails.length === 0) {
    return (
      <div className="p-4 text-center text-muted-foreground">
        <p>No recent emails found</p>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {emails.map((email) => (
        <div key={email.id} className="flex items-center group">
          <Avatar className="h-9 w-9">
            {email.avatarUrl ? (
              <AvatarImage src={email.avatarUrl} alt={`${email.senderName} avatar`} />
            ) : null}
            <AvatarFallback>{email.senderInitials}</AvatarFallback>
          </Avatar>
          <div className="ml-4 space-y-1 flex-1 min-w-0">
            <p className="text-sm font-medium leading-none">{email.senderName}</p>
            <p className="text-sm text-muted-foreground truncate">{email.subject}</p>
          </div>
          <div className="ml-auto font-medium text-right">
            <p className="text-sm">{email.time.relative}</p>
            <p className="text-xs text-muted-foreground hidden group-hover:block">{email.time.time}</p>
          </div>
        </div>
      ))}
    </div>
  )
}
