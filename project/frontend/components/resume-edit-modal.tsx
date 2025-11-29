"use client"

import { useState, useEffect, useCallback } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Loader2 } from "lucide-react"
import { updateResume, type ExperienceLevel, type ResumeData, type JobBookmarkData } from "@/lib/api/client"
import { toast } from "@/hooks/use-toast"

interface ResumeEditModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  resume: ResumeData | null
  bookmarks: JobBookmarkData[]
  onSuccess: () => void
}

const EXPERIENCE_OPTIONS: { value: ExperienceLevel; label: string }[] = [
  { value: "junior", label: "Junior Level" },
  { value: "mid_senior", label: "Mid-Senior Level" },
  { value: "director", label: "Director" },
  { value: "executive", label: "Executive" },
]

export function ResumeEditModal({ open, onOpenChange, resume, bookmarks, onSuccess }: ResumeEditModalProps) {
  const [resumeName, setResumeName] = useState("")
  const [experience, setExperience] = useState<ExperienceLevel>("junior")
  const [targetResume, setTargetResume] = useState(false)
  const [targetedJobId, setTargetedJobId] = useState<string | null>(null)
  const [isUpdating, setIsUpdating] = useState(false)

  // Initialize form with resume data
  useEffect(() => {
    if (resume && open) {
      setResumeName(resume.resume_name || resume.filename)
      setExperience(resume.experience || "junior")
      setTargetResume(!!resume.targeted_job_bookmark_id)
      setTargetedJobId(resume.targeted_job_bookmark_id)
    }
  }, [resume, open])

  // Clear targeted job when targeting is disabled
  useEffect(() => {
    if (!targetResume) {
      setTargetedJobId(null)
    }
  }, [targetResume])

  const handleClose = useCallback(() => {
    if (!isUpdating) {
      onOpenChange(false)
    }
  }, [isUpdating, onOpenChange])

  const handleSubmit = async () => {
    if (!resume) return

    if (!resumeName.trim()) {
      toast({
        title: "Name required",
        description: "Please enter a name for your resume.",
        variant: "destructive"
      })
      return
    }

    setIsUpdating(true)

    try {
      // When targeting is disabled, always set to null
      // When targeting is enabled, use the selected job (which should be valid)
      const targetedBookmarkId = targetResume ? targetedJobId : null

      await updateResume(resume.id, {
        resume_name: resumeName.trim(),
        experience,
        targeted_job_bookmark_id: targetedBookmarkId
      })

      toast({
        title: "Resume updated",
        description: "Your resume has been updated successfully."
      })

      onOpenChange(false)
      onSuccess()
    } catch (error) {
      toast({
        title: "Update failed",
        description: error instanceof Error ? error.message : "Failed to update resume",
        variant: "destructive"
      })
    } finally {
      setIsUpdating(false)
    }
  }

  if (!resume) return null

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="text-foreground">Edit Resume</DialogTitle>
          <DialogDescription className="text-muted-foreground">
            Update resume details and targeting options.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Resume Name */}
          <div className="space-y-2">
            <Label htmlFor="edit-resume-name" className="text-foreground">Resume Name</Label>
            <Input
              id="edit-resume-name"
              placeholder="e.g., Software Engineer Resume 2024"
              value={resumeName}
              onChange={(e) => setResumeName(e.target.value)}
              disabled={isUpdating}
            />
          </div>

          {/* Experience Level */}
          <div className="space-y-2">
            <Label className="text-foreground">Experience Level</Label>
            <Select
              value={experience}
              onValueChange={(value) => setExperience(value as ExperienceLevel)}
              disabled={isUpdating}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select experience level" />
              </SelectTrigger>
              <SelectContent>
                {EXPERIENCE_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Target Resume Toggle */}
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label className="text-foreground">Target your resume</Label>
              <p className="text-sm text-muted-foreground">
                Optimize for a specific job posting
              </p>
            </div>
            <Switch
              checked={targetResume}
              onCheckedChange={setTargetResume}
              disabled={isUpdating}
            />
          </div>

          {/* Job Selection (when targeting enabled) */}
          {targetResume && (
            <div className="space-y-2">
              <Label className="text-foreground">Select Target Job</Label>
              <Select
                value={targetedJobId || ""}
                onValueChange={setTargetedJobId}
                disabled={isUpdating}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a bookmarked job" />
                </SelectTrigger>
                <SelectContent>
                  {bookmarks.length === 0 ? (
                    <SelectItem value="none" disabled>
                      No bookmarked jobs available
                    </SelectItem>
                  ) : (
                    bookmarks.map((bookmark) => (
                      <SelectItem key={bookmark.bookmark_id} value={bookmark.bookmark_id}>
                        {bookmark.title} - {bookmark.company}
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
              {targetedJobId && resume.targeted_job_title && (
                <p className="text-sm text-muted-foreground">
                  Currently targeting: {resume.targeted_job_title} at {resume.targeted_job_company}
                </p>
              )}
            </div>
          )}

          {/* File Info (read-only) */}
          <div className="space-y-2">
            <Label className="text-foreground">File</Label>
            <div className="p-3 rounded-lg bg-muted/50 border">
              <p className="font-medium text-foreground">{resume.filename}</p>
              <p className="text-sm text-muted-foreground">
                {(resume.size / 1024 / 1024).toFixed(2)} MB • Uploaded {new Date(resume.uploaded_at).toLocaleDateString()}
              </p>
            </div>
            <p className="text-xs text-muted-foreground">
              To change the file, delete this resume and upload a new one.
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3">
          <Button
            variant="outline"
            onClick={handleClose}
            disabled={isUpdating}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isUpdating || !resumeName.trim()}
          >
            {isUpdating ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Updating...
              </>
            ) : (
              "Save Changes"
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

