"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { X, FileText, Target, Clock, Sparkles, RefreshCw, Copy, Check } from "lucide-react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import type { ResumeAnalysisResult, ResumeData } from "@/lib/api/client"

interface ResumeAnalysisCardProps {
  analysis: ResumeAnalysisResult
  resume: ResumeData
  onDismiss: () => void
  onAnalyzeAgain: () => void
  isAnalyzing?: boolean
}

export function ResumeAnalysisCard({
  analysis,
  resume,
  onDismiss,
  onAnalyzeAgain,
  isAnalyzing = false
}: ResumeAnalysisCardProps) {
  const [copied, setCopied] = useState(false)

  const cleanTips = (tips: string): string => {
    if (!tips) return ""
    
    // Clean up tips: Remove any JSON structure that might be included
    // Check if tips contains a JSON object and extract just the tips field if so
    let cleanedTips = tips.trim()
    
    // If tips starts with JSON structure, try to extract just the tips content
    if (cleanedTips.includes('"tips"') && (cleanedTips.includes('"match_score"') || cleanedTips.startsWith("{"))) {
      try {
        // Try to find and extract tips from JSON structure
        const jsonMatch = cleanedTips.match(/"tips"\s*:\s*"([^"]*(?:\\.[^"]*)*)"/)
        if (jsonMatch) {
          // Extract the tips content from JSON structure
          cleanedTips = jsonMatch[1]
            .replace(/\\n/g, "\n")
            .replace(/\\"/g, '"')
            .replace(/\\\\/g, "\\")
        } else {
          // Try parsing as JSON
          const jsonData = JSON.parse(cleanedTips)
          if (jsonData && typeof jsonData === "object" && "tips" in jsonData) {
            cleanedTips = jsonData.tips
          }
        }
      } catch (e) {
        // If parsing fails, try to remove JSON structure manually
        const jsonStart = cleanedTips.indexOf('"tips":')
        if (jsonStart !== -1) {
          const tipsStart = cleanedTips.indexOf('"', jsonStart + 7) + 1
          const tipsEnd = cleanedTips.lastIndexOf('"')
          if (tipsEnd > tipsStart) {
            cleanedTips = cleanedTips.substring(tipsStart, tipsEnd)
              .replace(/\\n/g, "\n")
              .replace(/\\"/g, '"')
              .replace(/\\\\/g, "\\")
          }
        }
      }
    }
    
    // Remove any trailing JSON structure that might be accidentally included
    const jsonEndMatch = cleanedTips.match(/^(.+?)(?:\s*\{[^}]*"match_score"[^}]*\}[^}]*)*$/)
    if (jsonEndMatch && jsonEndMatch[1] !== cleanedTips) {
      cleanedTips = jsonEndMatch[1].trim()
    }
    
    return cleanedTips
  }

  const handleCopyTips = async () => {
    const tipsToCopy = cleanTips(analysis.recommended_tips || "")
    
    try {
      await navigator.clipboard.writeText(tipsToCopy)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error("Failed to copy tips:", err)
    }
  }

  const formatLastAnalyzed = (timestamp: string | null) => {
    if (!timestamp) return "Recently"

    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return "Just now"
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? "s" : ""} ago`
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? "s" : ""} ago`

    return date.toLocaleDateString()
  }

  const formatUploadedDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  return (
    <Card className="border-primary/20 bg-gradient-to-br from-primary/5 to-primary/10">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            <CardTitle className="text-lg text-foreground">Resume Analysis Complete</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onAnalyzeAgain}
              disabled={isAnalyzing}
              className="h-8"
            >
              {isAnalyzing ? (
                <>
                  <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <RefreshCw className="h-3 w-3 mr-1" />
                  Analyze Again
                </>
              )}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={onDismiss}
              className="h-8 w-8 p-0"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Single column layout - Resume Info First */}
        <div className="space-y-6">
          {/* Analyzed Resume Section */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-primary" />
              <h3 className="font-semibold text-foreground">Analyzed Resume</h3>
            </div>

            <div className="space-y-4 p-4 rounded-lg bg-background/80 border">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Resume Name</p>
                  <p className="font-medium text-foreground">{resume.resume_name || resume.filename}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Experience Level</p>
                  <p className="font-medium text-foreground">
                    {resume.experience ? resume.experience.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'Not specified'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Uploaded</p>
                  <p className="font-medium text-foreground">{formatUploadedDate(resume.uploaded_at)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">File Size</p>
                  <p className="font-medium text-foreground">{(resume.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
              </div>

              {analysis.targeted_job_title && (
                <div className="flex items-center gap-2 pt-2 border-t">
                  <Target className="h-4 w-4 text-primary" />
                  <span className="text-sm text-muted-foreground">
                    Targeting: {analysis.targeted_job_title}
                    {analysis.targeted_job_company && ` at ${analysis.targeted_job_company}`}
                  </span>
                </div>
              )}

              {analysis.match_score !== null && analysis.match_score > 0 && (
                <div className="flex items-center gap-2 pt-2">
                  <Badge
                    className={`text-xs ${
                      analysis.match_score >= 84
                        ? "bg-green-500 hover:bg-green-600 text-white"
                        : analysis.match_score >= 65
                        ? "bg-yellow-500 hover:bg-yellow-600 text-white"
                        : "bg-gray-500 hover:bg-gray-600 text-white"
                    }`}
                  >
                    {Math.round(analysis.match_score)}% {analysis.targeted_job_title ? 'Match' : 'Overall Score'}
                  </Badge>
                </div>
              )}
            </div>
          </div>

          {/* AI Recommendations Section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-primary" />
                <h3 className="font-semibold text-foreground">AI Recommendations</h3>
              </div>
              <div className="flex items-center gap-3">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleCopyTips}
                  className="h-8 px-2"
                  title="Copy recommendations"
                >
                  {copied ? (
                    <>
                      <Check className="h-4 w-4 mr-1 text-green-600" />
                      <span className="text-xs">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4 mr-1" />
                      <span className="text-xs">Copy</span>
                    </>
                  )}
                </Button>
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  <span>Analyzed {formatLastAnalyzed(analysis.last_analyzed_at)}</span>
                </div>
              </div>
            </div>

            <div className="p-4 rounded-lg bg-background/80 border max-h-96 overflow-y-auto">
              <div className="prose prose-sm dark:prose-invert max-w-none prose-headings:text-foreground prose-p:text-foreground prose-strong:text-foreground prose-code:text-foreground text-sm text-foreground break-words">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    h1: ({ children }) => <h4 className="text-base font-semibold mb-3 mt-4 first:mt-0 break-words">{children}</h4>,
                    h2: ({ children }) => <h5 className="text-sm font-semibold mb-2 mt-3 break-words">{children}</h5>,
                    h3: ({ children }) => <h6 className="text-sm font-semibold mb-2 mt-2 break-words">{children}</h6>,
                    ul: ({ children }) => <ul className="list-disc list-inside space-y-1 mb-3 ml-4 break-words">{children}</ul>,
                    ol: ({ children }) => <ol className="list-decimal list-inside space-y-1 mb-3 ml-4 break-words">{children}</ol>,
                    li: ({ children }) => <li className="text-sm leading-relaxed break-words">{children}</li>,
                    p: ({ children }) => <p className="text-sm leading-relaxed mb-3 last:mb-0 break-words">{children}</p>,
                    strong: ({ children }) => <strong className="font-semibold break-words">{children}</strong>,
                    em: ({ children }) => <em className="italic break-words">{children}</em>,
                    code: ({ children }) => <code className="text-xs bg-muted px-1.5 py-0.5 rounded font-mono break-words">{children}</code>,
                    blockquote: ({ children }) => <blockquote className="border-l-4 border-primary/30 pl-4 italic text-muted-foreground my-2 break-words">{children}</blockquote>,
                  }}
                >
                  {cleanTips(analysis.recommended_tips || "")}
                </ReactMarkdown>
              </div>
            </div>
          </div>
        </div>

        {/* Footer with credits info */}
        {analysis.credits_used > 0 && (
          <div className="flex items-center justify-center pt-2 border-t">
            <p className="text-xs text-muted-foreground">
              Analysis used {analysis.credits_used} credit{analysis.credits_used > 1 ? "s" : ""}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
