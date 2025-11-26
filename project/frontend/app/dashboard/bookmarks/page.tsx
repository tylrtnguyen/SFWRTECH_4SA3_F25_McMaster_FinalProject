"use client"

import { useEffect, useState } from "react"
import dynamic from "next/dynamic"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { CheckCircle, XCircle, MoreHorizontal, Download, Eye, Edit, Trash2 } from "lucide-react"
import { getBookmarks, type JobBookmarkData } from "@/lib/api/client"

// Helper function to capitalize first letter
const capitalize = (str: string) => str.charAt(0).toUpperCase() + str.slice(1)

// Source mapping configuration
const sourceConfig = {
  linkedin: {
    label: "Linkedin",
    className: "bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-700"
  },
  document_upload: {
    label: "Uploaded Document",
    className: "bg-orange-100 text-orange-800 border-orange-300 dark:bg-orange-900/30 dark:text-orange-300 dark:border-orange-700"
  },
  manual: {
    label: "Manual",
    className: "bg-gray-100 text-gray-800 border-gray-300 dark:bg-gray-900/30 dark:text-gray-300 dark:border-gray-700"
  },
  // Default fallback
  default: {
    label: "Unknown",
    className: "bg-gray-100 text-gray-800 border-gray-300 dark:bg-gray-900/30 dark:text-gray-300 dark:border-gray-700"
  }
} as const

// Get source display info
const getSourceDisplay = (source: string) => {
  return sourceConfig[source as keyof typeof sourceConfig] || sourceConfig.default
}

export default function BookmarksPage() {
  const [bookmarks, setBookmarks] = useState<JobBookmarkData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [mounted, setMounted] = useState(false)

  // Reusable header component
  const PageHeader = () => (
    <div>
      <h1 className="text-3xl font-bold tracking-tight text-text-primary dark:text-[#e4e6eb]">Bookmarks</h1>
    </div>
  )

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!mounted) return // Only run on client after mount

    const fetchBookmarks = async () => {
      try {
        const data = await getBookmarks()
        setBookmarks(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load bookmarks')
        console.error('Bookmarks fetch failed:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchBookmarks()
  }, [mounted])

  const exportToCSV = () => {
    if (!mounted) return // Prevent SSR issues

    if (bookmarks.length === 0) {
      alert("No bookmarks to export")
      return
    }

    const headers = [
      "Title",
      "Company",
      "Location",
      "Source",
      "Is Genuine",
      "Confidence Score",
      "Application Status",
      "Created At"
    ]

    const csvData = bookmarks.map((bookmark, index) => [
      bookmark.title,
      bookmark.company,
      bookmark.location || "N/A",
      getSourceDisplay(bookmark.source).label,
      bookmark.is_authentic ? "Yes" : "No",
      bookmark.confidence_score ? `${bookmark.confidence_score}%` : "N/A",
      bookmark.application_status
        .split('_')
        .map(word => capitalize(word))
        .join(' '),
      new Date(bookmark.created_at).toISOString().split('T')[0] // Use consistent date format
    ])

    const csvContent = [
      headers.join(","),
      ...csvData.map(row => row.map(cell => `"${cell.replace(/"/g, '""')}"`).join(",")) // Escape quotes properly
    ].join("\n")

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement("a")
    const url = URL.createObjectURL(blob)
    link.setAttribute("href", url)
    link.setAttribute("download", `job_bookmarks_${new Date().toISOString().split('T')[0]}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    alert("Bookmarks exported successfully")
  }

  const handleView = (bookmark: JobBookmarkData) => {
    if (!mounted) return
    // TODO: Navigate to bookmark details page
    alert("View functionality coming soon")
  }

  const handleEdit = (bookmark: JobBookmarkData) => {
    if (!mounted) return
    // TODO: Open edit modal or navigate to edit page
    alert("Edit functionality coming soon")
  }

  const handleDelete = (bookmark: JobBookmarkData) => {
    if (!mounted) return
    // TODO: Implement delete functionality with confirmation
    alert("Delete functionality coming soon")
  }

  if (!mounted || loading) {
    return (
      <div className="space-y-6">
        <PageHeader />
        <div className="h-32 bg-gray-200 dark:bg-gray-800 rounded-lg animate-pulse"></div>
        <div className="h-96 bg-gray-200 dark:bg-gray-800 rounded-lg animate-pulse"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <PageHeader />
        <div className="text-center py-12">
          <p className="text-red-500 mb-4">Error: {error}</p>
          <Button onClick={() => window.location.reload()}>
            Try Again
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader />

      {/* Info Card */}
      <Card className="bg-white dark:bg-[#22262e] border-none"><CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Job Bookmarks Overview</CardTitle>
              <CardDescription>
                You have {bookmarks.length} saved job{bookmarks.length !== 1 ? 's' : ''} in your bookmarks
              </CardDescription>
            </div>
            <Button onClick={exportToCSV} variant="outline" className="gap-2">
              <Download className="h-4 w-4" />
              Export CSV
            </Button>
          </div>
      </CardHeader></Card>
      

      {/* Bookmarks Table */}
      <Card>
        <CardHeader>
          <CardTitle>Saved Jobs</CardTitle>
          <CardDescription>
            Manage your bookmarked jobs and track your application progress
          </CardDescription>
        </CardHeader>
        <CardContent>
          {bookmarks.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-text-secondary dark:text-[#b0b3b8] mb-4">
                No bookmarks found. Start by analyzing some jobs!
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">#</TableHead>
                  <TableHead>Title</TableHead>
                  <TableHead>Company</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Source</TableHead>
                  <TableHead>Is Genuine</TableHead>
                  <TableHead>Confidence</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-12">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {bookmarks.map((bookmark, index) => (
                  <TableRow key={bookmark.bookmark_id}>
                    <TableCell className="font-medium">{index + 1}</TableCell>
                    <TableCell className="max-w-xs">
                      <div className="truncate" title={bookmark.title}>
                        {bookmark.title}
                      </div>
                    </TableCell>
                    <TableCell>{bookmark.company}</TableCell>
                    <TableCell>{bookmark.location || "N/A"}</TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={getSourceDisplay(bookmark.source).className}
                      >
                        {getSourceDisplay(bookmark.source).label}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {bookmark.is_authentic !== null ? (
                        bookmark.is_authentic ? (
                          <div className="flex items-center gap-2">
                            <CheckCircle className="h-4 w-4 text-green-600" />
                            <span className="text-green-700 dark:text-green-300 font-medium">
                              Genuine Job
                            </span>
                          </div>
                        ) : (
                          <div className="flex items-center gap-2">
                            <XCircle className="h-4 w-4 text-red-600" />
                            <span className="text-red-700 dark:text-red-300">
                              Suspicious
                            </span>
                          </div>
                        )
                      ) : (
                        <span className="text-gray-500">Not Analyzed</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {bookmark.confidence_score !== null ? (
                        <span className={`font-medium ${
                          bookmark.confidence_score >= 80 ? 'text-green-600' :
                          bookmark.confidence_score >= 60 ? 'text-yellow-600' :
                          'text-red-600'
                        }`}>
                          {bookmark.confidence_score}%
                        </span>
                      ) : (
                        <span className="text-gray-500">N/A</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          bookmark.application_status === 'interested' ? 'default' :
                          bookmark.application_status === 'applied' ? 'secondary' :
                          bookmark.application_status === 'interviewing' ? 'outline' :
                          'destructive'
                        }
                      >
                        {bookmark.application_status
                          .split('_')
                          .map(word => capitalize(word))
                          .join(' ')
                        }
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" className="h-8 w-8 p-0">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleView(bookmark)}>
                            <Eye className="mr-2 h-4 w-4" />
                            View Details
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleEdit(bookmark)}>
                            <Edit className="mr-2 h-4 w-4" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => handleDelete(bookmark)}
                            className="text-red-600"
                          >
                            <Trash2 className="mr-2 h-4 w-4" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

