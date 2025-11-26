"use client"

import { CheckCircle2, XCircle, AlertTriangle, Bookmark as BookmarkIcon } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import type { JobUrlSearchResponse } from "@/lib/api/client"

interface JobSearchResultsProps {
  result: JobUrlSearchResponse
}

export function JobSearchResults({ result }: JobSearchResultsProps) {
  const { job_data, analysis } = result
  
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
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-text-primary dark:text-[#e4e6eb] mb-2">
              {job_data.title}
            </CardTitle>
            <CardDescription className="text-text-secondary dark:text-[#b0b3b8]">
              {job_data.company} {job_data.location && `• ${job_data.location}`}
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
        
        {/* Evidence/Reasoning */}
        {analysis.evidence && (
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-text-primary dark:text-[#e4e6eb]">
              Analysis Evidence:
            </h4>
            <p className="text-sm text-text-secondary dark:text-[#b0b3b8] bg-bg-secondary dark:bg-[#22262e] p-3 rounded-md">
              {analysis.evidence}
            </p>
          </div>
        )}
        
        {/* Job Description Preview */}
        {job_data.description && (
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-text-primary dark:text-[#e4e6eb]">
              Job Description:
            </h4>
            <p className="text-sm text-text-secondary dark:text-[#b0b3b8] line-clamp-3">
              {job_data.description}
            </p>
          </div>
        )}
        
        {/* Credits Used */}
        <div className="flex items-center gap-2 text-xs text-text-tertiary dark:text-[#8a8d91]">
          <span>Credits used: {analysis.credits_used}</span>
        </div>
        
        {/* Actions */}
        <div className="flex gap-2 pt-2">
          <Button
            variant="outline"
            size="sm"
            className="flex-1"
            onClick={() => {
              if (job_data.source_url) {
                window.open(job_data.source_url, "_blank")
              }
            }}
          >
            View Original Posting
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled
            className="opacity-50 cursor-not-allowed"
          >
            <BookmarkIcon className="mr-2 h-4 w-4" />
            Already Bookmarked
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}


