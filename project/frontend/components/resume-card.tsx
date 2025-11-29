"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { 
  MoreVertical, 
  Pencil, 
  Copy, 
  Lightbulb, 
  Download, 
  Trash2,
  FileText,
  Target,
  Loader2
} from "lucide-react"
import {
  type ResumeData,
  deleteResume,
  duplicateResume,
  getResumeDownloadUrl,
  getResumePreviewUrl
} from "@/lib/api/client"
import { toast } from "@/hooks/use-toast"

interface ResumeCardProps {
  resume: ResumeData
  onEdit: (resume: ResumeData) => void
  onAnalyze: (resume: ResumeData) => void
  onRefresh: () => void
  viewMode: "grid" | "list"
  isAnalyzing?: boolean
}

function formatTimeAgo(dateString: string): string {
  try {
    // Parse the date string - Supabase returns ISO strings
    const date = new Date(dateString)

    // Ensure we have valid dates
    if (isNaN(date.getTime())) {
      return "Unknown date"
    }

    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    // For very recent uploads, show "Just uploaded"
    if (diffMins < 1) return "Just uploaded"

    // For items less than 1 hour old, show minutes
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? "s" : ""} ago`

    // For items less than 24 hours old, show hours
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`

    // For items less than 7 days old, show days
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? "s" : ""} ago`

    // For older items, show the date
    return date.toLocaleDateString()
  } catch (error) {
    console.warn("Error formatting date:", error, dateString)
    return "Unknown date"
  }
}

function getExperienceLabel(experience: string | null): string {
  switch (experience) {
    case "junior": return "Junior Level"
    case "mid_senior": return "Mid-Senior Level"
    case "director": return "Director"
    case "executive": return "Executive"
    default: return "Not specified"
  }
}

export function ResumeCard({ resume, onEdit, onAnalyze, onRefresh, viewMode, isAnalyzing }: ResumeCardProps) {
  const [isDeleting, setIsDeleting] = useState(false)
  const [isDuplicating, setIsDuplicating] = useState(false)
  const [isDownloading, setIsDownloading] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [previewError, setPreviewError] = useState(false)

  // Load preview URL on mount
  useState(() => {
    const loadPreview = async () => {
      try {
        const url = await getResumePreviewUrl(resume.id)
        setPreviewUrl(url)
      } catch {
        setPreviewError(true)
      }
    }
    loadPreview()
  })

  const handleDelete = async () => {
    setIsDeleting(true)
    try {
      await deleteResume(resume.id)
      toast({
        title: "Resume deleted",
        description: "Your resume has been deleted successfully."
      })
      onRefresh()
    } catch (error) {
      toast({
        title: "Delete failed",
        description: error instanceof Error ? error.message : "Failed to delete resume",
        variant: "destructive"
      })
    } finally {
      setIsDeleting(false)
      setShowDeleteDialog(false)
    }
  }

  const handleDuplicate = async () => {
    setIsDuplicating(true)
    try {
      await duplicateResume(resume.id)
      toast({
        title: "Resume duplicated",
        description: "A copy of your resume has been created."
      })
      onRefresh()
    } catch (error) {
      toast({
        title: "Duplicate failed",
        description: error instanceof Error ? error.message : "Failed to duplicate resume",
        variant: "destructive"
      })
    } finally {
      setIsDuplicating(false)
    }
  }

  const handleAnalyze = async () => {
    await onAnalyze(resume)
  }

  const handleDownload = async () => {
    setIsDownloading(true)
    try {
      const url = await getResumeDownloadUrl(resume.id)
      // Open download URL in new tab
      window.open(url, "_blank")
      toast({
        title: "Download started",
        description: "Your resume download has started."
      })
    } catch (error) {
      toast({
        title: "Download failed",
        description: error instanceof Error ? error.message : "Failed to download resume",
        variant: "destructive"
      })
    } finally {
      setIsDownloading(false)
    }
  }

  const isLoading = isDeleting || isDuplicating || (isAnalyzing ?? false) || isDownloading

  if (viewMode === "list") {
    return (
      <>
        <Card className="p-4 hover:shadow-md transition-shadow">
          <div className="flex items-center gap-4">
            {/* Icon */}
            <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
              <FileText className="h-6 w-6 text-primary" />
            </div>

            {/* Info */}
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-foreground truncate">
                {resume.resume_name || resume.filename}
              </h3>
              <p className="text-sm text-muted-foreground">
                {getExperienceLabel(resume.experience)} • {formatTimeAgo(resume.uploaded_at)}
              </p>
              {resume.targeted_job_title && (
                <div className="flex items-center gap-1 mt-1">
                  <Target className="h-3 w-3 text-primary" />
                  <span className="text-xs text-primary">
                    {resume.targeted_job_title} at {resume.targeted_job_company}
                  </span>
                </div>
              )}
            </div>

            {/* Match Score */}
            {resume.match_score !== null && (
              <div className="flex-shrink-0 text-center px-4">
                <div className="text-2xl font-bold text-primary">{Math.round(resume.match_score)}%</div>
                <div className="text-xs text-muted-foreground">Match</div>
              </div>
            )}

            {/* Actions */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" disabled={isLoading}>
                  {isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <MoreVertical className="h-4 w-4" />
                  )}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => onEdit(resume)}>
                  <Pencil className="mr-2 h-4 w-4" />
                  Edit
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleDuplicate} disabled={isDuplicating}>
                  <Copy className="mr-2 h-4 w-4" />
                  Duplicate
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleAnalyze} disabled={isAnalyzing}>
                  <Lightbulb className="mr-2 h-4 w-4" />
                  Get Tips
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleDownload} disabled={isDownloading}>
                  <Download className="mr-2 h-4 w-4" />
                  Download PDF
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem 
                  onClick={() => setShowDeleteDialog(true)}
                  className="text-destructive focus:text-destructive"
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </Card>

        {/* Delete Confirmation Dialog */}
        <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete Resume</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to delete &quot;{resume.resume_name || resume.filename}&quot;? 
                This action cannot be undone.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={handleDelete}
                disabled={isDeleting}
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              >
                {isDeleting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Deleting...
                  </>
                ) : (
                  "Delete"
                )}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </>
    )
  }

  // Grid view
  return (
    <>
      <Card className="overflow-hidden hover:shadow-lg transition-shadow group">
        {/* Preview Area */}
        <div className="aspect-[3/4] bg-muted relative overflow-hidden">
          {previewUrl && !previewError ? (
            <iframe
              src={`${previewUrl}#toolbar=0&navpanes=0&scrollbar=0&statusbar=0&messages=0&view=FitH,top`}
              className="w-full h-full pointer-events-none"
              title={`Preview of ${resume.resume_name || resume.filename}`}
              style={{ pointerEvents: 'none', border: 'none' }}
            />
          ) : (
            <div className="w-full h-full flex flex-col items-center justify-center text-muted-foreground">
              <FileText className="h-16 w-16 mb-2" />
              <span className="text-sm">Preview unavailable</span>
            </div>
          )}
          
          {/* Target Badge */}
          {resume.targeted_job_title && (
            <div className="absolute top-2 left-2 bg-background/90 backdrop-blur-sm px-2 py-1 rounded-md flex items-center gap-1 max-w-[140px]">
              <Target className="h-3 w-3 text-primary flex-shrink-0" />
              <span className="text-xs font-medium text-foreground truncate">
                {resume.targeted_job_title}
              </span>
            </div>
          )}

          {/* Match Score Badge - Adjust position if target badge exists */}
          {resume.match_score !== null && (
            <div className={`absolute ${resume.targeted_job_title ? 'top-10' : 'top-2'} right-2 px-2 py-1 rounded-md text-sm font-semibold ${
              resume.match_score >= 84
                ? 'bg-green-500 text-white'
                : resume.match_score >= 65
                ? 'bg-yellow-500 text-white'
                : 'bg-gray-500 text-white'
            }`}>
              {Math.round(resume.match_score)}% Match
            </div>
          )}
        </div>

        {/* Info Area */}
        <div className="p-4">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0 flex-1">
              <h3 className="font-semibold text-foreground truncate">
                {resume.resume_name || resume.filename}
              </h3>
              <p className="text-sm text-muted-foreground">
                {formatTimeAgo(resume.uploaded_at)}
              </p>
            </div>
            
            {/* 3-dot menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="flex-shrink-0" disabled={isLoading}>
                  {isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <MoreVertical className="h-4 w-4" />
                  )}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => onEdit(resume)}>
                  <Pencil className="mr-2 h-4 w-4" />
                  Edit
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleDuplicate} disabled={isDuplicating}>
                  <Copy className="mr-2 h-4 w-4" />
                  Duplicate
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleAnalyze} disabled={isAnalyzing}>
                  <Lightbulb className="mr-2 h-4 w-4" />
                  Get Tips
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleDownload} disabled={isDownloading}>
                  <Download className="mr-2 h-4 w-4" />
                  Download PDF
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem 
                  onClick={() => setShowDeleteDialog(true)}
                  className="text-destructive focus:text-destructive"
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </Card>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Resume</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete &quot;{resume.resume_name || resume.filename}&quot;? 
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={isDeleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isDeleting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Deleting...
                </>
              ) : (
                "Delete"
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}

