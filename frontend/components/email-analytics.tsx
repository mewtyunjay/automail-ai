"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Skeleton } from "@/components/ui/skeleton"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { CalendarIcon, DollarSignIcon, ClockIcon, CheckIcon, AlertCircleIcon } from "lucide-react"

// Define interfaces for the analytics data
interface FinancialTransaction {
  id?: string
  email_id: string
  type: string
  amount: number
  currency: string
  description: string
  date: string
  category: string
  recurring: boolean
  source_subject?: string
  source_sender?: string
}

interface FinancialSummary {
  total_income: number
  total_expenses: number
  net_balance: number
  currency: string
  top_categories: {
    [category: string]: number
  }
  recurring_expenses: number
  recent_transactions: FinancialTransaction[]
}

interface Meeting {
  title: string
  date: string
  time: string
  duration: string
  location: string
  attendees?: string[]
  description?: string
  email_id: string
  source_subject?: string
  source_sender?: string
}

interface Todo {
  task: string
  deadline?: string
  priority?: string
  context?: string
  email_id: string
  email_thread_id?: string
  source_subject?: string
  sender?: string
  extracted_at?: string
}

interface EmailNeedsReply {
  email_id: string
  thread_id: string
  subject: string
  sender: string
  date: string
  snippet: string
}

interface EmailAnalytics {
  finances: {
    transactions: FinancialTransaction[]
    summary: FinancialSummary
  }
  meetings: Meeting[]
  todos: Todo[]
  needs_reply: EmailNeedsReply[]
}

export function EmailAnalytics() {
  const [analytics, setAnalytics] = useState<EmailAnalytics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [retryCount, setRetryCount] = useState(0)

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true)
        const response = await fetch('http://localhost:8000/email-analytics?max_emails=20')
        
        if (!response.ok) {
          const errorText = await response.text().catch(() => 'Unknown error')
          throw new Error(`Error fetching analytics (${response.status}): ${errorText}`)
        }
        
        const data = await response.json()
        if (data.status === "success" && data.analytics) {
          setAnalytics(data.analytics)
          setError(null)
        } else {
          throw new Error(data.message || "Failed to get analytics data")
        }
      } catch (err) {
        console.error('Failed to fetch email analytics:', err)
        setError(`Failed to load analytics: ${err instanceof Error ? err.message : 'Unknown error'}`)
      } finally {
        setLoading(false)
      }
    }

    fetchAnalytics()
  }, [retryCount])

  // Format currency
  const formatCurrency = (amount: number, currency: string = "USD") => {
    return new Intl.NumberFormat('en-US', { 
      style: 'currency', 
      currency: currency,
      minimumFractionDigits: 2
    }).format(amount)
  }

  // Format date
  const formatDate = (dateStr: string) => {
    if (!dateStr) return ""
    try {
      const date = new Date(dateStr)
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        year: 'numeric'
      })
    } catch (e) {
      return dateStr
    }
  }

  if (loading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <Skeleton className="h-5 w-40" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-64 w-full" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <Skeleton className="h-5 w-40" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-64 w-full" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <Skeleton className="h-5 w-40" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-64 w-full" />
          </CardContent>
        </Card>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 text-center">
        <p className="text-red-500 mb-3">{error}</p>
        <Button 
          onClick={() => setRetryCount(prev => prev + 1)}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
        >
          Retry
        </Button>
      </div>
    )
  }

  if (!analytics) {
    return (
      <div className="p-4 text-center text-muted-foreground">
        <p>No analytics data available</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {/* Financial Summary Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <DollarSignIcon className="mr-2 h-5 w-5" />
              Financial Overview
            </CardTitle>
            <CardDescription>Summary of your financial transactions</CardDescription>
          </CardHeader>
          <CardContent>
            {analytics.finances.summary && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Income</p>
                    <p className="text-xl font-bold text-green-600">
                      {formatCurrency(analytics.finances.summary.total_income || 0, analytics.finances.summary.currency)}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Expenses</p>
                    <p className="text-xl font-bold text-red-600">
                      {formatCurrency(analytics.finances.summary.total_expenses || 0, analytics.finances.summary.currency)}
                    </p>
                  </div>
                </div>
                <div className="pt-2 border-t">
                  <p className="text-sm text-muted-foreground">Net Balance</p>
                  <p className={`text-2xl font-bold ${analytics.finances.summary.net_balance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatCurrency(analytics.finances.summary.net_balance || 0, analytics.finances.summary.currency)}
                  </p>
                </div>
                {analytics.finances.transactions && analytics.finances.transactions.length > 0 && (
                  <div className="pt-2 border-t">
                    <p className="text-sm font-medium mb-2">Recent Transactions</p>
                    <div className="space-y-2">
                      {analytics.finances.transactions.slice(0, 3).map((transaction, i) => (
                        <div key={i} className="flex justify-between items-center">
                          <div className="flex-1 truncate">
                            <p className="text-sm truncate">{transaction.description}</p>
                            <p className="text-xs text-muted-foreground">{formatDate(transaction.date)}</p>
                          </div>
                          <p className={`text-sm font-medium ${transaction.type === 'income' ? 'text-green-600' : 'text-red-600'}`}>
                            {transaction.type === 'income' ? '+' : '-'}{formatCurrency(transaction.amount, transaction.currency)}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
            {(!analytics.finances.summary || Object.keys(analytics.finances.summary).length === 0) && (
              <p className="text-center text-muted-foreground py-8">No financial data found</p>
            )}
          </CardContent>
        </Card>

        {/* Upcoming Meetings Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <CalendarIcon className="mr-2 h-5 w-5" />
              Upcoming Meetings
            </CardTitle>
            <CardDescription>Meetings extracted from your emails</CardDescription>
          </CardHeader>
          <CardContent>
            {analytics.meetings && analytics.meetings.length > 0 ? (
              <div className="space-y-4">
                {analytics.meetings.slice(0, 4).map((meeting, i) => (
                  <div key={i} className="border rounded-lg p-3 space-y-2">
                    <div className="flex justify-between items-start">
                      <h4 className="font-medium">{meeting.title}</h4>
                      <Badge variant="outline">{meeting.location}</Badge>
                    </div>
                    <div className="flex items-center text-sm text-muted-foreground">
                      <ClockIcon className="mr-1 h-4 w-4" />
                      <span>{formatDate(meeting.date)} • {meeting.time} ({meeting.duration})</span>
                    </div>
                    {meeting.description && (
                      <p className="text-sm text-muted-foreground">{meeting.description}</p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center text-muted-foreground py-8">No upcoming meetings found</p>
            )}
          </CardContent>
        </Card>

        {/* Todo List Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <CheckIcon className="mr-2 h-5 w-5" />
              Action Items
            </CardTitle>
            <CardDescription>Tasks extracted from your emails</CardDescription>
          </CardHeader>
          <CardContent>
            {analytics.todos && analytics.todos.length > 0 ? (
              <div className="space-y-2">
                {analytics.todos.slice(0, 6).map((todo, i) => (
                  <div key={i} className="flex items-start space-x-2 p-2 border-b last:border-0">
                    <div className="mt-0.5">
                      <CheckIcon className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div className="flex-1 space-y-1">
                      <p className="text-sm font-medium">{todo.task}</p>
                      <div className="flex flex-wrap gap-2">
                        {todo.priority && (
                          <Badge variant={todo.priority === 'high' ? 'destructive' : (todo.priority === 'medium' ? 'default' : 'outline')}>
                            {todo.priority}
                          </Badge>
                        )}
                        {todo.deadline && (
                          <Badge variant="outline" className="flex items-center">
                            <CalendarIcon className="mr-1 h-3 w-3" />
                            {formatDate(todo.deadline)}
                          </Badge>
                        )}
                      </div>
                      {todo.context && (
                        <p className="text-xs text-muted-foreground">{todo.context}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center text-muted-foreground py-8">No action items found</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Emails Needing Reply */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <AlertCircleIcon className="mr-2 h-5 w-5" />
            Emails Needing Reply
          </CardTitle>
          <CardDescription>Emails that may require your attention</CardDescription>
        </CardHeader>
        <CardContent>
          {analytics.needs_reply && analytics.needs_reply.length > 0 ? (
            <div className="space-y-4">
              {analytics.needs_reply.map((email, i) => (
                <div key={i} className="flex items-start space-x-4 p-3 border rounded-lg">
                  <Avatar className="h-10 w-10">
                    <AvatarFallback>{email.sender.substring(0, 2).toUpperCase()}</AvatarFallback>
                  </Avatar>
                  <div className="flex-1 space-y-1">
                    <div className="flex justify-between">
                      <p className="font-medium">{email.subject}</p>
                      <p className="text-sm text-muted-foreground">{formatDate(email.date)}</p>
                    </div>
                    <p className="text-sm text-muted-foreground">{email.snippet}</p>
                    <Button size="sm" className="mt-2">Generate Reply</Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-muted-foreground py-4">No emails requiring reply found</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
