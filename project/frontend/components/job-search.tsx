"use client"

import { useState } from "react"
import { Search, Link as LinkIcon, FileText, Upload, Bookmark, Sparkles, Loader2, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { JobForm, type JobFormData } from "@/components/job-form"
import { searchJobByUrl, submitManualJob, uploadJobDocument, type JobUrlSearchResponse } from "@/lib/api/client"
import { JobSearchResults } from "@/components/job-search-results"

export function JobSearch() {
  const [url, setUrl] = useState("")
  const [file, setFile] = useState<File | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [loadingMessage, setLoadingMessage] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [searchResult, setSearchResult] = useState<JobUrlSearchResponse | null>(null)

  // URL validation regex patterns
  const linkedinUrlPattern = /^https?:\/\/(www\.)?linkedin\.com\/jobs\/view\//
  const indeedUrlPattern = /^https?:\/\/([a-z]{2}\.)?(www\.)?indeed\.com\/viewjob\?jk=/

  const validateJobUrl = (url: string): boolean => {
    if (!url.trim()) return false
    const normalizedUrl = url.startsWith("http") ? url : `https://${url}`
    return linkedinUrlPattern.test(normalizedUrl) || indeedUrlPattern.test(normalizedUrl)
  }

  const handleUrlSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSearchResult(null)
    
    // Validate URL format
    if (!validateJobUrl(url)) {
      setError("Please enter a valid LinkedIn or Indeed job URL (e.g., https://www.linkedin.com/jobs/view/... or https://ca.indeed.com/viewjob?jk=...)")
      return
    }
    
    setIsLoading(true)
    setLoadingMessage("Verifying URL safety...")
    
    try {
      // Normalize URL
      const normalizedUrl = url.startsWith("http") ? url : `https://${url}`
      
      setLoadingMessage("Scraping job data...")
      const result = await searchJobByUrl(normalizedUrl)
      
      setLoadingMessage("Analyzing authenticity...")
      // Small delay to show the loading message
      await new Promise((resolve) => setTimeout(resolve, 500))
      
      setSearchResult(result)
      setUrl("") // Clear input on success
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to search job. Please try again."
      setError(errorMessage)
    } finally {
      setIsLoading(false)
      setLoadingMessage("")
    }
  }

  const handleManualSubmit = async (data: JobFormData) => {
    setError(null)
    setSearchResult(null)

    setIsLoading(true)
    setLoadingMessage("Analyzing job authenticity...")

    try {
      // Map JobFormData to API format
      const apiData = {
        job_title: data.jobTitle,
        company: data.company,
        location: data.location,
        industry: data.industry,
        source: data.source,
        description: data.jobDescription
      }

      const result = await submitManualJob(apiData)

      setLoadingMessage("Processing results...")
      // Small delay to show the loading message
      await new Promise((resolve) => setTimeout(resolve, 500))

      setSearchResult(result)
      // Only clear form on successful analysis display
      // This will be handled by the form's reset function when results are shown
    } catch (err) {
      let errorMessage = "Failed to submit job. Please try again."

      // Provide more educational error messages
      if (err instanceof Error) {
        if (err.message.includes("Insufficient credits")) {
          errorMessage = "You don't have enough credits to analyze this job. Please purchase more credits to continue."
        } else if (err.message.includes("Invalid")) {
          errorMessage = "There was an issue with your job details. Please check all required fields and try again."
        } else if (err.message.includes("network") || err.message.includes("fetch")) {
          errorMessage = "Network error occurred. Please check your connection and try again."
        } else {
          errorMessage = err.message
        }
      }

      setError(errorMessage)
      // Don't reset form on error - keep values so user can fix them
    } finally {
      setIsLoading(false)
      setLoadingMessage("")
    }
  }

  const validateFile = (file: File): string | null => {
    const maxSize = 20 * 1024 * 1024 // 20MB
    const allowedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/msword',
      'text/plain'
    ]

    if (file.size > maxSize) {
      return 'File size must be less than 20MB'
    }

    if (!allowedTypes.includes(file.type)) {
      return 'Only PDF, DOC, DOCX, and TXT files are supported'
    }

    return null
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      const error = validateFile(selectedFile)
      if (error) {
        setError(error)
        setFile(null)
      } else {
        setFile(selectedFile)
        setError(null)
      }
    }
  }

  const processDocument = async () => {
    if (!file) return

    setIsLoading(true)
    setLoadingMessage("Analyzing document...")
    setError(null)
    setSearchResult(null)

    try {
      const result = await uploadJobDocument(file)
      setSearchResult(result)
      setFile(null) // Clear file after successful processing

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Document processing failed')
    } finally {
      setIsLoading(false)
      setLoadingMessage("")
    }
  }

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle className="text-text-primary dark:text-[#e4e6eb]">Search and Add Job</CardTitle>
        <CardDescription className="text-text-secondary dark:text-[#b0b3b8]">
          Search for jobs by URL, manually input job details, or upload a job posting
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <Tabs defaultValue="url" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger
              value="url"
              className="bg-bg-primary data-[state=active]:bg-primary-400 dark:data-[state=active]:bg-primary-400 data-[state=active]:text-white dark:data-[state=active]:text-white"
            >
              <LinkIcon className="mr-2 h-4 w-4" />
              By URL
            </TabsTrigger>
            <TabsTrigger
              value="manual"
              className="bg-bg-primary data-[state=active]:bg-primary-400 dark:data-[state=active]:bg-primary-400 data-[state=active]:text-white dark:data-[state=active]:text-white"
            >
              <FileText className="mr-2 h-4 w-4" />
              Manual Input
            </TabsTrigger>
            <TabsTrigger
              value="upload"
              className="bg-bg-primary data-[state=active]:bg-primary-400 dark:data-[state=active]:bg-primary-400 data-[state=active]:text-white dark:data-[state=active]:text-white"
            >
              <Upload className="mr-2 h-4 w-4" />
              Upload
            </TabsTrigger>
          </TabsList>

          <TabsContent value="url" className="mt-4 space-y-4">
            <form onSubmit={handleUrlSubmit} className="flex gap-2">
              <Input
                type="url"
                placeholder="Enter LinkedIn or Indeed job URL (e.g., https://www.linkedin.com/jobs/view/... or https://ca.indeed.com/viewjob?jk=...)"
                value={url}
                onChange={(e) => {
                  setUrl(e.target.value)
                  setError(null)
                  setSearchResult(null)
                }}
                disabled={isLoading}
                className="flex-1 placeholder:text-text-secondary dark:placeholder:text-[#8993A4]"
              />
              <Button type="submit" disabled={isLoading || !url.trim()}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Search className="mr-2 h-4 w-4" />
                    Search
                  </>
                )}
              </Button>
            </form>

            {isLoading && loadingMessage && (
              <div className="flex items-center gap-2 text-sm text-text-secondary dark:text-[#b0b3b8]">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>{loadingMessage}</span>
              </div>
            )}
          </TabsContent>

          <TabsContent value="manual" className="mt-4">
            <JobForm onSubmit={handleManualSubmit} isSubmitting={isLoading} />

            {isLoading && loadingMessage && (
              <div className="flex items-center gap-2 text-sm text-text-secondary dark:text-[#b0b3b8] mt-4">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>{loadingMessage}</span>
              </div>
            )}
          </TabsContent>

          <TabsContent value="upload" className="mt-4">
            <div className="space-y-4">
              <div className="flex items-center justify-center rounded-lg border-2 border-dashed border-border-default dark:border-[#3a3f4b] bg-bg-primary dark:bg-[#1a1d23] placeholder:text-text-secondary dark:placeholder:text-[#f4f5f7] p-8">
                <div className="text-center">
                  <Upload className="mx-auto h-12 w-12 text-muted-foreground" />
                  <div className="mt-4">
                    <label htmlFor="file-upload" className="cursor-pointer">
                      <span className="text-sm font-medium text-primary">
                        Click to upload
                      </span>
                      <span className="text-sm text-muted-foreground">
                        {" "}
                        or drag and drop
                      </span>
                    </label>
                    <input
                      id="file-upload"
                      name="file-upload"
                      type="file"
                      className="sr-only"
                      accept=".pdf,.doc,.docx,.txt"
                      onChange={handleFileUpload}
                    />
                  </div>
                  <p className="mt-2 text-xs text-muted-foreground">
                    PDF, DOC, DOCX, or TXT (MAX. 20MB)
                  </p>
                  {file && (
                    <p className="mt-2 text-sm text-text-primary dark:text-[#e4e6eb]">
                      Uploaded: {file.name}
                    </p>
                  )}
                </div>
              </div>
              {file && (
                  <Button
                    className="w-full bg-primary-600 dark:bg-primary-400 hover:bg-primary-700 dark:hover:bg-primary-500 text-white"
                    onClick={processDocument}
                    disabled={!file || isLoading}
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <Sparkles className="mr-2 h-4 w-4" />
                        Process and bookmark
                      </>
                    )}
                  </Button>
                  
              )}
            </div>
          </TabsContent>
        </Tabs>

        {/* Shared Results and Error Display */}
        <div className="space-y-4">
          {error && (
            <div className="flex items-start gap-2 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {searchResult && (
            <JobSearchResults
              result={searchResult}
              onAcknowledge={() => {
                setSearchResult(null)
                setError(null)
              }}
            />
          )}
        </div>
      </CardContent>
    </Card>
  )
}

