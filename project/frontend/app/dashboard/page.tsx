"use client"

import { Bookmark, Briefcase, XCircle, FileText, Coins, TrendingUp } from "lucide-react"
import { StatCard } from "@/components/stat-card"
import { JobSearch } from "@/components/job-search"

export default function DashboardPage() {
  // Mock data - replace with actual API calls
  const stats = {
    bookmarks: 12,
    inInterview: 5,
    failedInterview: 2,
    avgMatchScore: 87,
    creditsRemaining: 150,
    potentialJobs: 24,
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-text-primary dark:text-[#e4e6eb]">Dashboard</h1>
        <p className="text-text-secondary dark:text-[#b0b3b8]">
          Welcome back! Here's an overview of your job search progress.
        </p>
      </div>

      {/* Job Search Section */}
      <JobSearch />

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <StatCard
          title="Job Bookmarks"
          value={stats.bookmarks}
          description="Saved jobs"
          icon={Bookmark}
          trend={{ value: "+3 this week", isPositive: true }}
        />
        <StatCard
          title="In Interview"
          value={stats.inInterview}
          description="Active applications"
          icon={Briefcase}
          trend={{ value: "+2 this week", isPositive: true }}
        />
        <StatCard
          title="Failed Interview"
          value={stats.failedInterview}
          description="Past interviews"
          icon={XCircle}
        />
        <StatCard
          title="Avg Match Score"
          value={`${stats.avgMatchScore}%`}
          description="Active resume"
          icon={FileText}
          trend={{ value: "+5% this month", isPositive: true }}
          className="bg-success/10 dark:bg-success/20 border-success/30"
        />
        <StatCard
          title="Credits Remaining"
          value={stats.creditsRemaining}
          description="Available credits"
          icon={Coins}
          className="bg-accent/10 dark:bg-accent/20 border-accent/30"
        />
        <StatCard
          title="Potential Jobs"
          value={stats.potentialJobs}
          description="Ready to apply"
          icon={TrendingUp}
          trend={{ value: "+8 this week", isPositive: true }}
          className="bg-secondary/10 dark:bg-secondary/20 border-secondary/30"
        />
      </div>
    </div>
  )
}

