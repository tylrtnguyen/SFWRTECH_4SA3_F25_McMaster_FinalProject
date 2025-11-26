"use client"

import { useState } from "react"
import { Search, Link as LinkIcon, FileText, Upload, Bookmark, Sparkles, Loader2, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { JobForm, type JobFormData } from "@/components/job-form"
import { searchJobByUrl, type JobUrlSearchResponse } from "@/lib/api/client"
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
    // TODO: Implement manual job input
    console.log("Submitting manual job:", data)
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
      // TODO: Implement file upload
      console.log("Uploading file:", selectedFile.name)
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
      <CardContent>
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
            
            {error && (
              <div className="flex items-start gap-2 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}
            
            {searchResult && (
              <JobSearchResults result={searchResult} />
            )}
          </TabsContent>

          <TabsContent value="manual" className="mt-4">
            <JobForm onSubmit={handleManualSubmit} />
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
                    PDF, DOC, DOCX, or TXT (MAX. 10MB)
                  </p>
                  {file && (
                    <p className="mt-2 text-sm text-text-primary dark:text-[#e4e6eb]">
                      Uploaded: {file.name}
                    </p>
                  )}
                </div>
              </div>
              {file && (
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                  <Button
                    className="bg-primary-600 dark:bg-primary-400 hover:bg-primary-700 dark:hover:bg-primary-500 text-white"
                    onClick={() => {
                      // TODO: Implement process file
                      console.log("Processing file:", file.name)
                    }}
                  >
                    <Sparkles className="mr-2 h-4 w-4" />
                    Process
                  </Button>
                  <Button
                    variant="secondary"
                    className="bg-secondary-600 dark:bg-secondary-400 hover:bg-secondary-600/80 dark:hover:bg-secondary-400/80 text-white"
                    onClick={() => {
                      // TODO: Implement bookmark file
                      console.log("Bookmarking file:", file.name)
                    }}
                  >
                    <Bookmark className="mr-2 h-4 w-4" />
                    Bookmark
                  </Button>
                  <Button
                    className="bg-accent-warning dark:bg-[#d9c760] hover:bg-accent-warning/90 dark:hover:bg-[#d9c760]/90 text-[#172B4D] dark:text-[#1a1d23]"
                    onClick={() => {
                      // TODO: Implement bookmark and process file
                      console.log("Bookmarking and processing file:", file.name)
                    }}
                  >
                    <Sparkles className="mr-2 h-4 w-4" />
                    <Bookmark className="mr-2 h-4 w-4" />
                    Bookmark & Process
                  </Button>
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}

