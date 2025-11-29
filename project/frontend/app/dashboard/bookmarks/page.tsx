"use client"

import { useEffect, useState } from "react"
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
import ReactMarkdown from "react-markdown"
import { getBookmarks, getBookmarkDetail, updateBookmark, deleteBookmark, type JobBookmarkData } from "@/lib/api/client"
import { useToast } from "@/hooks/use-toast"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

// Helper function to capitalize first letter
const capitalize = (str: string) => str.charAt(0).toUpperCase() + str.slice(1)

// Helper function to truncate text
const truncateText = (text: string, maxLength: number) => {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + "..."
}

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
  const { toast } = useToast()

  // Modal states
  const [viewModalOpen, setViewModalOpen] = useState(false)
  const [editModalOpen, setEditModalOpen] = useState(false)
  const [selectedBookmark, setSelectedBookmark] = useState<JobBookmarkData | null>(null)
  const [editingBookmark, setEditingBookmark] = useState<JobBookmarkData | null>(null)
  const [isUpdating, setIsUpdating] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [bookmarkToDelete, setBookmarkToDelete] = useState<JobBookmarkData | null>(null)
  const [descriptionExpanded, setDescriptionExpanded] = useState(false)
  const [analysisExpanded, setAnalysisExpanded] = useState(false)

  // Reusable header component
  const PageHeader = (bookmarksLength: number | undefined) => (
    <div>
      <div className="space-y-3">
        <h1 className="text-3xl font-bold tracking-tight text-text-primary dark:text-[#e4e6eb]">
        Bookmarks
        </h1>
        <p className="text-text-secondary dark:text-[#b0b3b8]">
        {bookmarksLength !== undefined ? `You have ${bookmarksLength} saved job${bookmarksLength !== 1 ? 's' : ''} in your bookmarks.` : ''}
        </p>
      </div>
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
      toast({
        title: "No bookmarks to export",
        description: "Add some bookmarks first before exporting.",
        variant: "destructive",
      })
      return
    }

    const headers = [
      "#",
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
      index + 1,
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
      ...csvData.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(",")) // Escape quotes properly
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

    toast({
      title: "Export successful",
      description: `Downloaded ${bookmarks.length} bookmarks to CSV.`,
      variant: "success",
    })
  }

  const handleView = async (bookmark: JobBookmarkData) => {
    if (!mounted) return

    try {
      const detail = await getBookmarkDetail(bookmark.bookmark_id)
      setSelectedBookmark(detail)
      setViewModalOpen(true)
    } catch (error) {
      toast({
        title: "Failed to load details",
        description: "Unable to fetch bookmark details. Please try again.",
        variant: "destructive",
      })
    }
  }

  const handleEdit = (bookmark: JobBookmarkData) => {
    if (!mounted) return
    setEditingBookmark({ ...bookmark }) // Create a copy for editing
    setEditModalOpen(true)
  }

  const handleDelete = async () => {
    if (!bookmarkToDelete || !mounted) return

    try {
      await deleteBookmark(bookmarkToDelete.bookmark_id)

      // Remove from local state
      setBookmarks(prev => prev.filter(b => b.bookmark_id !== bookmarkToDelete.bookmark_id))

      toast({
        title: "Bookmark deleted",
        description: `"${bookmarkToDelete.title}" has been removed from your bookmarks.`,
        variant: "success",
      })
    } catch (error) {
      console.error("Failed to delete bookmark:", error)
      toast({
        title: "Delete failed",
        description: "Unable to delete bookmark. Please try again.",
        variant: "destructive",
      })
    } finally {
      setDeleteDialogOpen(false)
      setBookmarkToDelete(null)
    }
  }

  const openDeleteDialog = (bookmark: JobBookmarkData) => {
    setBookmarkToDelete(bookmark)
    setDeleteDialogOpen(true)
  }

  const handleUpdateBookmark = async () => {
    if (!editingBookmark) return

    setIsUpdating(true)
    try {
      const updated = await updateBookmark(editingBookmark.bookmark_id, {
        title: editingBookmark.title,
        company: editingBookmark.company,
        location: editingBookmark.location,
        application_status: editingBookmark.application_status,
        description: editingBookmark.description
      })

      // Update the bookmarks list
      setBookmarks(prev => prev.map(b =>
        b.bookmark_id === updated.bookmark_id ? updated : b
      ))

      setEditModalOpen(false)
      setEditingBookmark(null)
      toast({
        title: "Bookmark updated",
        description: `"${editingBookmark.title}" has been updated successfully.`,
        variant: "success",
      })
    } catch (error) {
      toast({
        title: "Update failed",
        description: "Unable to update bookmark. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsUpdating(false)
    }
  }

  if (!mounted || loading) {
    return (
      <div className="space-y-8 px-4 md:px-8 lg:px-16 xl:px-24 max-w-7xl mx-auto">
        {PageHeader(bookmarks.length)}
        <div className="h-32 bg-gray-200 dark:bg-gray-800 rounded-lg animate-pulse"></div>
        <div className="h-96 bg-gray-200 dark:bg-gray-800 rounded-lg animate-pulse"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-8 px-4 md:px-8 lg:px-16 xl:px-24 max-w-7xl mx-auto">
        {PageHeader(bookmarks.length)}
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
    <div className="space-y-8 px-4 md:px-8 lg:px-12 xl:px-16 max-w-7xl mx-auto">
      {PageHeader(bookmarks.length)}

      {/* Info Card */}
      <Card className="bg-white dark:bg-[#22262e] border-none"><CardHeader>
          <div className="flex items-center justify-between">
      <div>
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
                        className={
                          bookmark.application_status === 'interested'
                            ? 'bg-blue-500 hover:bg-blue-600 text-white'
                            : bookmark.application_status === 'applied'
                            ? 'bg-purple-500 hover:bg-purple-600 text-white'
                            : bookmark.application_status === 'interviewing'
                            ? 'bg-white hover:bg-gray-50 text-black border-gray-300'
                            : bookmark.application_status === 'interviewed_passed'
                            ? 'bg-green-500 hover:bg-green-600 text-white'
                            : bookmark.application_status === 'interviewed_failed'
                            ? 'bg-red-500 hover:bg-red-600 text-white'
                            : 'bg-gray-500 hover:bg-gray-600 text-white'
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
                            onClick={() => openDeleteDialog(bookmark)}
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

      {/* View Details Modal */}
      <Dialog open={viewModalOpen} onOpenChange={(open) => {
        setViewModalOpen(open)
        if (!open) {
          setDescriptionExpanded(false)
          setAnalysisExpanded(false)
        }
      }}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{selectedBookmark?.title}</DialogTitle>
            <DialogDescription>{selectedBookmark?.company}</DialogDescription>
          </DialogHeader>

          {selectedBookmark && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <dt className="text-sm font-medium text-muted-foreground">Location</dt>
                  <dd className="text-sm text-foreground">{selectedBookmark.location || "Not specified"}</dd>
                </div>
                <div className="space-y-1">
                  <dt className="text-sm font-medium text-muted-foreground">Source</dt>
                  <dd className="text-sm text-foreground">{selectedBookmark.source}</dd>
                </div>
                <div className="space-y-1">
                  <dt className="text-sm font-medium text-muted-foreground">Application Status</dt>
                  <dd className="text-sm text-foreground">{selectedBookmark.application_status.replace('_', ' ')}</dd>
                </div>
                <div className="space-y-1">
                  <dt className="text-sm font-medium text-muted-foreground">Created</dt>
                  <dd className="text-sm text-foreground">{new Date(selectedBookmark.created_at).toLocaleDateString()}</dd>
                </div>
              </div>

              {selectedBookmark.source_url && (
                <div className="space-y-1">
                  <dt className="text-sm font-medium text-muted-foreground">Source URL</dt>
                  <dd>
                    <a
                      href={selectedBookmark.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 underline text-sm break-all"
                    >
                      {selectedBookmark.source_url}
                    </a>
                  </dd>
                </div>
              )}

              {selectedBookmark.description && (
                <div className="space-y-2">
                  <dt className="text-sm font-medium text-muted-foreground">Description</dt>
                  <dd className="text-sm text-foreground prose prose-sm max-w-none dark:prose-invert">
                    <ReactMarkdown>
                      {descriptionExpanded
                        ? selectedBookmark.description
                        : truncateText(selectedBookmark.description, 2500)
                      }
                    </ReactMarkdown>
                    {selectedBookmark.description.length > 2500 && (
                      <button
                        onClick={() => setDescriptionExpanded(!descriptionExpanded)}
                        className="text-primary hover:text-primary/80 text-sm font-medium mt-2 transition-colors"
                      >
                        {descriptionExpanded ? "View Less" : "View More"}
                      </button>
                    )}
                  </dd>
                </div>
              )}

              {selectedBookmark.is_authentic !== null && (
                <div className="space-y-2">
                  <dt className="text-sm font-medium text-muted-foreground">Authenticity Analysis</dt>
                  <dd>
                    <div className="p-3 bg-muted rounded-md border">
                      <div className="flex items-center gap-2 mb-2">
                        {selectedBookmark.is_authentic ? (
                          <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400" />
                        ) : (
                          <XCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
                        )}
                        <span className="font-medium text-foreground">
                          {selectedBookmark.is_authentic ? "Genuine Job" : "Suspicious"}
                        </span>
                        {selectedBookmark.confidence_score && (
                          <span className="text-sm text-muted-foreground">
                            ({selectedBookmark.confidence_score}% confidence)
                          </span>
                        )}
                      </div>
                      {selectedBookmark.analysis_evidence && (
                        <div className="text-sm text-foreground prose prose-sm max-w-none dark:prose-invert">
                          <ReactMarkdown>
                            {analysisExpanded
                              ? selectedBookmark.analysis_evidence
                              : truncateText(selectedBookmark.analysis_evidence, 2500)
                            }
                          </ReactMarkdown>
                          {selectedBookmark.analysis_evidence.length > 2500 && (
                            <button
                              onClick={() => setAnalysisExpanded(!analysisExpanded)}
                              className="text-primary hover:text-primary/80 text-sm font-medium mt-2 transition-colors"
                            >
                              {analysisExpanded ? "View Less" : "View More"}
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  </dd>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Edit Modal */}
      <Dialog open={editModalOpen} onOpenChange={setEditModalOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Bookmark</DialogTitle>
            <DialogDescription>
              Update the bookmark information
            </DialogDescription>
          </DialogHeader>

          {editingBookmark && (
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-foreground">Job Title</label>
                <Input
                  value={editingBookmark.title}
                  onChange={(e) => setEditingBookmark(prev => prev ?
                    { ...prev, title: e.target.value } : null
                  )}
                />
              </div>

              <div>
                <label className="text-sm font-medium text-foreground">Company</label>
                <Input
                  value={editingBookmark.company}
                  onChange={(e) => setEditingBookmark(prev => prev ?
                    { ...prev, company: e.target.value } : null
                  )}
                />
              </div>

              <div>
                <label className="text-sm font-medium text-foreground">Location</label>
                <Input
                  value={editingBookmark.location || ""}
                  onChange={(e) => setEditingBookmark(prev => prev ?
                    { ...prev, location: e.target.value } : null
                  )}
                />
              </div>

              <div>
                <label className="text-sm font-medium text-foreground">Application Status</label>
                <Select
                  value={editingBookmark.application_status}
                  onValueChange={(value: any) =>
                    setEditingBookmark(prev => prev ?
                      { ...prev, application_status: value } : null
                    )
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="interested">Interested</SelectItem>
                    <SelectItem value="applied">Applied</SelectItem>
                    <SelectItem value="interviewing">Interviewing</SelectItem>
                    <SelectItem value="interviewed_passed">Interviewed - Passed</SelectItem>
                    <SelectItem value="interviewed_failed">Interviewed - Failed</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="text-sm font-medium text-foreground">Description</label>
                <Textarea
                  value={editingBookmark.description || ""}
                  onChange={(e) => setEditingBookmark(prev => prev ?
                    { ...prev, description: e.target.value } : null
                  )}
                  rows={6}
                  placeholder="Enter job description..."
                />
              </div>

              <div className="flex gap-2 pt-4">
                <Button
                  onClick={handleUpdateBookmark}
                  disabled={isUpdating}
                  className="flex-1"
                >
                  {isUpdating ? "Updating..." : "Update Bookmark"}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setEditModalOpen(false)}
                  className="flex-1"
                >
                  Cancel
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Modal */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Bookmark</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete &quot;{bookmarkToDelete?.title}&quot;? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}

