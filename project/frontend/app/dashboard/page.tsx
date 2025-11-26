"use client"

import { useEffect, useState } from "react"
import { Bookmark, Briefcase, XCircle, FileText, Coins, TrendingUp } from "lucide-react"
import { StatCard } from "@/components/stat-card"
import { JobSearch } from "@/components/job-search"
import { getDashboardStats } from "@/lib/api/client"

interface DashboardStats {
  job_bookmarks: number
  in_interview: number
  failed_interview: number
  avg_match_score: number | null
  credits_remaining: number
  potential_jobs: number
  job_bookmarks_change: number | null
  in_interview_change: number | null
  avg_match_score_change: number | null
  potential_jobs_change: number | null
  _isMockData?: boolean // Internal flag to track if this is mock data
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchStats = async () => {
      try {
        console.log('Fetching dashboard stats...')
        const data = await getDashboardStats()
        console.log('Dashboard stats received:', data)
        setStats(data)
        setError(null) // Clear any previous errors
      } catch (err) {
        console.error('Dashboard stats fetch failed:', err)
        setError(err instanceof Error ? err.message : 'Failed to load dashboard stats')
        // Fallback to mock data if API fails
        console.log('Using fallback mock data due to API error')
        setStats({
          job_bookmarks: 12,
          in_interview: 5,
          failed_interview: 2,
          avg_match_score: 87,
          credits_remaining: 150,
          potential_jobs: 24,
          job_bookmarks_change: 3.2,
          in_interview_change: 2.1,
          avg_match_score_change: 5.0,
          potential_jobs_change: 8.5,
          _isMockData: true
        })
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
  }, [])

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-text-primary dark:text-[#e4e6eb]">Dashboard</h1>
          <p className="text-text-secondary dark:text-[#b0b3b8]">
            Loading your dashboard...
          </p>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-32 bg-gray-200 dark:bg-gray-800 rounded-lg animate-pulse"></div>
          ))}
        </div>
      </div>
    )
  }

  if (error && !stats) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-text-primary dark:text-[#e4e6eb]">Dashboard</h1>
          <p className="text-red-500">Error: {error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-text-primary dark:text-[#e4e6eb]">
          Dashboard
          {stats?._isMockData && (
            <span className="ml-2 text-xs bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200 px-2 py-1 rounded">
              DEMO DATA
            </span>
          )}
        </h1>
        <p className="text-text-secondary dark:text-[#b0b3b8]">
          Welcome back! Here's an overview of your job search progress.
          {stats?._isMockData && " (Currently showing demo data - check console for API errors)"}
        </p>
      </div>

      {/* Job Search Section */}
      <JobSearch />

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <StatCard
          title="Job Bookmarks"
          value={stats!.job_bookmarks}
          description="Saved jobs"
          icon={Bookmark}
          trend={stats!.job_bookmarks_change !== null ? {
            value: Math.abs(stats!.job_bookmarks_change).toString(),
            isPositive: stats!.job_bookmarks_change >= 0,
            isPercentage: true
          } : undefined}
        />
        <StatCard
          title="In Interview"
          value={stats!.in_interview}
          description="Active applications"
          icon={Briefcase}
          trend={stats!.in_interview_change !== null ? {
            value: Math.abs(stats!.in_interview_change).toString(),
            isPositive: stats!.in_interview_change >= 0,
            isPercentage: true
          } : undefined}
        />
        <StatCard
          title="Failed Interview"
          value={stats!.failed_interview}
          description="Past interviews"
          icon={XCircle}
        />
        <StatCard
          title="Avg Match Score"
          value={stats!.avg_match_score ? `${stats!.avg_match_score}%` : "N/A"}
          description="Active resume"
          icon={FileText}
          trend={stats!.avg_match_score_change !== null ? {
            value: Math.abs(stats!.avg_match_score_change).toString(),
            isPositive: stats!.avg_match_score_change >= 0,
            isPercentage: true
          } : undefined}
          className="bg-success/10 dark:bg-success/20 border-success/30"
        />
        <StatCard
          title="Credits Remaining"
          value={stats!.credits_remaining}
          description="Available credits"
          icon={Coins}
          className="bg-accent/10 dark:bg-accent/20 border-accent/30"
        />
        <StatCard
          title="Potential Jobs"
          value={stats!.potential_jobs}
          description="Ready to apply"
          icon={TrendingUp}
          trend={stats!.potential_jobs_change !== null ? {
            value: Math.abs(stats!.potential_jobs_change).toString(),
            isPositive: stats!.potential_jobs_change >= 0,
            isPercentage: true
          } : undefined}
          className="bg-secondary/10 dark:bg-secondary/20 border-secondary/30"
        />
      </div>
    </div>
  )
}

