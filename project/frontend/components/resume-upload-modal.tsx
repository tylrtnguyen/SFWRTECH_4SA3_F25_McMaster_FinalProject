"use client"

import { useState, useCallback } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Upload, FileText, X, Loader2 } from "lucide-react"
import { createResume, type ExperienceLevel, type JobBookmarkData } from "@/lib/api/client"
import { toast } from "@/hooks/use-toast"

interface ResumeUploadModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  bookmarks: JobBookmarkData[]
  onSuccess: () => void
}

const EXPERIENCE_OPTIONS: { value: ExperienceLevel; label: string }[] = [
  { value: "junior", label: "Junior Level" },
  { value: "mid_senior", label: "Mid-Senior Level" },
  { value: "director", label: "Director" },
  { value: "executive", label: "Executive" },
]

export function ResumeUploadModal({ open, onOpenChange, bookmarks, onSuccess }: ResumeUploadModalProps) {
  const [resumeName, setResumeName] = useState("")
  const [experience, setExperience] = useState<ExperienceLevel>("junior")
  const [targetResume, setTargetResume] = useState(false)
  const [targetedJobId, setTargetedJobId] = useState<string | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)

  const resetForm = useCallback(() => {
    setResumeName("")
    setExperience("junior")
    setTargetResume(false)
    setTargetedJobId(null)
    setFile(null)
    setIsDragging(false)
  }, [])

  const handleClose = useCallback(() => {
    if (!isUploading) {
      resetForm()
      onOpenChange(false)
    }
  }, [isUploading, resetForm, onOpenChange])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile && isValidFile(droppedFile)) {
      setFile(droppedFile)
      if (!resumeName) {
        setResumeName(droppedFile.name.replace(/\.[^/.]+$/, ""))
      }
    } else {
      toast({
        title: "Invalid file",
        description: "Please upload a PDF or DOCX file.",
        variant: "destructive"
      })
    }
  }, [resumeName])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile && isValidFile(selectedFile)) {
      setFile(selectedFile)
      if (!resumeName) {
        setResumeName(selectedFile.name.replace(/\.[^/.]+$/, ""))
      }
    } else if (selectedFile) {
      toast({
        title: "Invalid file",
        description: "Please upload a PDF or DOCX file.",
        variant: "destructive"
      })
    }
  }, [resumeName])

  const isValidFile = (file: File): boolean => {
    const validTypes = [
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    return validTypes.includes(file.type)
  }

  const handleSubmit = async () => {
    if (!file) {
      toast({
        title: "No file selected",
        description: "Please select a resume file to upload.",
        variant: "destructive"
      })
      return
    }

    if (!resumeName.trim()) {
      toast({
        title: "Name required",
        description: "Please enter a name for your resume.",
        variant: "destructive"
      })
      return
    }

    setIsUploading(true)

    try {
      await createResume(file, {
        resume_name: resumeName.trim(),
        experience,
        targeted_job_bookmark_id: targetResume ? targetedJobId : null
      })

      toast({
        title: "Resume uploaded",
        description: "Your resume has been uploaded successfully."
      })

      resetForm()
      onOpenChange(false)
      onSuccess()
    } catch (error) {
      toast({
        title: "Upload failed",
        description: error instanceof Error ? error.message : "Failed to upload resume",
        variant: "destructive"
      })
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="text-foreground">Upload New Resume</DialogTitle>
          <DialogDescription className="text-muted-foreground">
            Upload your resume and configure targeting options.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Resume Name */}
          <div className="space-y-2">
            <Label htmlFor="resume-name" className="text-foreground">Resume Name</Label>
            <Input
              id="resume-name"
              placeholder="e.g., Software Engineer Resume 2024"
              value={resumeName}
              onChange={(e) => setResumeName(e.target.value)}
              disabled={isUploading}
            />
          </div>

          {/* Experience Level */}
          <div className="space-y-2">
            <Label className="text-foreground">Experience Level</Label>
            <Select
              value={experience}
              onValueChange={(value) => setExperience(value as ExperienceLevel)}
              disabled={isUploading}
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
              disabled={isUploading}
            />
          </div>

          {/* Job Selection (when targeting enabled) */}
          {targetResume && (
            <div className="space-y-2">
              <Label className="text-foreground">Select Target Job</Label>
              <Select
                value={targetedJobId || ""}
                onValueChange={setTargetedJobId}
                disabled={isUploading}
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
            </div>
          )}

          {/* File Upload Zone */}
          <div className="space-y-2">
            <Label className="text-foreground">Resume File</Label>
            <div
              className={`
                border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer
                ${isDragging 
                  ? "border-primary bg-primary/5" 
                  : "border-muted-foreground/25 hover:border-primary/50"
                }
                ${file ? "bg-muted/50" : ""}
              `}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => document.getElementById("file-input")?.click()}
            >
              <input
                id="file-input"
                type="file"
                accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                onChange={handleFileSelect}
                className="hidden"
                disabled={isUploading}
              />
              
              {file ? (
                <div className="flex items-center justify-center gap-3">
                  <FileText className="h-8 w-8 text-primary" />
                  <div className="text-left">
                    <p className="font-medium text-foreground">{file.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={(e) => {
                      e.stopPropagation()
                      setFile(null)
                    }}
                    disabled={isUploading}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ) : (
                <div className="space-y-2">
                  <Upload className="h-10 w-10 mx-auto text-muted-foreground" />
                  <div>
                    <p className="font-medium text-foreground">
                      Drag and drop or click to upload
                    </p>
                    <p className="text-sm text-muted-foreground">
                      PDF or DOCX (max 20MB)
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3">
          <Button
            variant="outline"
            onClick={handleClose}
            disabled={isUploading}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isUploading || !file || !resumeName.trim()}
          >
            {isUploading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Uploading...
              </>
            ) : (
              "Save Resume"
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

