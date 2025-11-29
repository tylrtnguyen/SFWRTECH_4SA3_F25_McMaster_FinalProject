"use client"

import { CheckCircle2, XCircle, AlertTriangle, Bookmark as BookmarkIcon, AlertOctagon } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import ReactMarkdown from "react-markdown"
import type { JobUrlSearchResponse } from "@/lib/api/client"

interface JobSearchResultsProps {
  result: JobUrlSearchResponse
  onAcknowledge?: () => void
}

export function JobSearchResults({ result, onAcknowledge }: JobSearchResultsProps) {
  const { job_data, analysis, bookmarked, already_bookmarked } = result
  
  // Get display data - use extracted_data from analysis if job_data is null (for fake jobs)
  const displayTitle = job_data?.title || "Job Analysis Result"
  const displayCompany = job_data?.company || analysis.extracted_data?.company || "Unknown Company"
  const displayLocation = job_data?.location || analysis.extracted_data?.location
  const displayIndustry = analysis.extracted_data?.industry
  const displaySourceUrl = job_data?.source_url
  const displayDescription = job_data?.description
  
  const getAuthenticityBadge = () => {
    if (analysis.is_authentic === null) {
      return (
        <Badge variant="secondary" className="bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">
          <AlertTriangle className="mr-1 h-3 w-3" />
          Unknown
        </Badge>
      )
    }
    
    if (analysis.is_authentic) {
      return (
        <Badge className="bg-success-600 text-white dark:bg-success-400 dark:text-[#1a1d23]">
          <CheckCircle2 className="mr-1 h-3 w-3" />
          Real Job
        </Badge>
      )
    } else {
      return (
        <Badge variant="destructive">
          <XCircle className="mr-1 h-3 w-3" />
          Fake/Scam
        </Badge>
      )
    }
  }
  
  const getConfidenceColor = (score: number | null) => {
    if (score === null) return "text-text-secondary dark:text-[#b0b3b8]"
    if (score >= 80) return "text-success-600 dark:text-success-400"
    if (score >= 60) return "text-yellow-600 dark:text-yellow-400"
    return "text-destructive"
  }
  
  return (
    <Card className="mt-4 border-border-default dark:border-[#3a3f4b]">
      {/* Info Banner for Already Bookmarked Jobs */}
      {already_bookmarked && (
        <div className="bg-primary/10 border-b border-primary/20 px-4 py-3 flex items-center gap-2">
          <BookmarkIcon className="h-5 w-5 text-primary" />
          <span className="text-sm font-medium text-primary">
            This job is already in your bookmarks. No credits were used.
          </span>
        </div>
      )}
      
      {/* Warning Banner for Fake Jobs */}
      {analysis.is_authentic === false && !already_bookmarked && (
        <div className="bg-destructive/10 border-b border-destructive/20 px-4 py-3 flex items-center gap-2">
          <AlertOctagon className="h-5 w-5 text-destructive" />
          <span className="text-sm font-medium text-destructive">
            Warning: This job posting has been identified as potentially fake or a scam. It has not been bookmarked.
          </span>
        </div>
      )}
      
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-text-primary dark:text-[#e4e6eb] mb-2">
              {displayTitle}
            </CardTitle>
            <CardDescription className="text-text-secondary dark:text-[#b0b3b8]">
              <span className="font-bold text-primary">{displayCompany}</span>
              {displayLocation && ` • ${displayLocation}`}
              {displayIndustry && ` • ${displayIndustry}`}
            </CardDescription>
          </div>
          {getAuthenticityBadge()}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Confidence Score */}
        {analysis.confidence_score !== null && (
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-text-secondary dark:text-[#b0b3b8]">
              Confidence Score:
            </span>
            <span className={`text-sm font-bold ${getConfidenceColor(analysis.confidence_score)}`}>
              {Number(analysis.confidence_score).toFixed(1)}%
            </span>
          </div>
        )}
        
        {/* Evidence/Reasoning with Markdown Rendering */}
        {analysis.evidence && (
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-text-primary dark:text-[#e4e6eb]">
              Analysis Evidence:
            </h4>
            <div className="text-sm text-text-secondary dark:text-[#b0b3b8] bg-bg-secondary dark:bg-[#22262e] p-4 rounded-md prose prose-sm dark:prose-invert max-w-none prose-headings:text-text-primary dark:prose-headings:text-[#e4e6eb] prose-strong:text-text-primary dark:prose-strong:text-[#e4e6eb] prose-li:marker:text-text-secondary">
              <ReactMarkdown
                components={{
                  h1: ({ children }) => <h3 className="text-base font-bold mt-4 mb-2 text-text-primary dark:text-[#e4e6eb]">{children}</h3>,
                  h2: ({ children }) => <h4 className="text-sm font-bold mt-3 mb-2 text-text-primary dark:text-[#e4e6eb]">{children}</h4>,
                  h3: ({ children }) => <h5 className="text-sm font-semibold mt-2 mb-1 text-text-primary dark:text-[#e4e6eb]">{children}</h5>,
                  p: ({ children }) => <p className="mb-2 leading-relaxed">{children}</p>,
                  ul: ({ children }) => <ul className="list-disc pl-5 mb-2 space-y-1">{children}</ul>,
                  ol: ({ children }) => <ol className="list-decimal pl-5 mb-2 space-y-1">{children}</ol>,
                  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
                  strong: ({ children }) => <strong className="font-semibold text-text-primary dark:text-[#e4e6eb]">{children}</strong>,
                }}
              >
              {analysis.evidence}
              </ReactMarkdown>
            </div>
          </div>
        )}
        
        {/* Job Description Preview */}
        {displayDescription && (
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-text-primary dark:text-[#e4e6eb]">
              Job Description:
            </h4>
            <p className="text-sm text-text-secondary dark:text-[#b0b3b8] line-clamp-3">
              {displayDescription}
            </p>
          </div>
        )}
        
        {/* Credits Used */}
        <div className="flex items-center gap-2 text-sm font-medium text-text-tertiary dark:text-[#8a8d91]">
          <span>
            Credits used: {analysis.credits_used}
            {already_bookmarked && " (previously analyzed)"}
          </span>
        </div>
        
        {/* Actions */}
        <div className="flex gap-2 pt-2">
          {displaySourceUrl && (
          <Button
            variant="outline"
            size="sm"
            className="flex-1"
            onClick={() => {
                window.open(displaySourceUrl, "_blank")
            }}
          >
            View Original Posting
          </Button>
          )}
          {bookmarked ? (
          <Button
            variant="outline"
            size="sm"
            disabled
            className="opacity-50 cursor-not-allowed"
          >
            <BookmarkIcon className="mr-2 h-4 w-4" />
              {already_bookmarked ? "Already Bookmarked" : "Bookmarked"}
            </Button>
          ) : (
            <Button
              variant="outline"
              size="sm"
              disabled
              className="opacity-50 cursor-not-allowed text-destructive border-destructive/50"
            >
              <XCircle className="mr-2 h-4 w-4" />
              Not Bookmarked
            </Button>
          )}
          {onAcknowledge && (
            <Button
              variant="secondary"
              size="sm"
              onClick={onAcknowledge}
              className="bg-secondary-600 hover:bg-secondary-700 text-white"
            >
              Acknowledge
          </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}


