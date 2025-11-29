"use client";

import { useState, useEffect, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  FileText,
  Upload,
  Grid3X3,
  List,
  Loader2,
  RefreshCw,
} from "lucide-react";
import {
  getResumes,
  getBookmarks,
  analyzeResume,
  type ResumeData,
  type JobBookmarkData,
  type ResumeAnalysisResult,
} from "@/lib/api/client";
import { ResumeUploadModal } from "@/components/resume-upload-modal";
import { ResumeEditModal } from "@/components/resume-edit-modal";
import { ResumeCard } from "@/components/resume-card";
import { ResumeAnalysisCard } from "@/components/resume-analysis-card";
import { toast } from "@/hooks/use-toast";

// Helper function to format experience level
function getExperienceLabel(experience: string | null): string {
  switch (experience) {
    case "junior":
      return "Junior Level";
    case "mid_senior":
      return "Mid-Senior Level";
    case "director":
      return "Director";
    case "executive":
      return "Executive";
    default:
      return "Not specified";
  }
}

type ViewMode = "grid" | "list";

export default function ResumePage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [resumes, setResumes] = useState<ResumeData[]>([]);
  const [bookmarks, setBookmarks] = useState<JobBookmarkData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingResume, setEditingResume] = useState<ResumeData | null>(null);
  const [analysisResult, setAnalysisResult] =
    useState<ResumeAnalysisResult | null>(null);
  const [analyzingResume, setAnalyzingResume] = useState<ResumeData | null>(
    null
  );
  const [lastAnalyzedResume, setLastAnalyzedResume] =
    useState<ResumeData | null>(null);
  const [mounted, setMounted] = useState(false);

  // Ensure client-side only rendering
  useEffect(() => {
    setMounted(true);
  }, []);

  // Check for upload parameter to open modal automatically
  useEffect(() => {
    const upload = searchParams.get("upload");
    if (upload === "true" && mounted) {
      setShowUploadModal(true);
      // Clean up URL parameter
      router.replace("/dashboard/resume", undefined);
    }
  }, [searchParams, mounted, router]);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [resumesData, bookmarksData] = await Promise.all([
        getResumes(),
        getBookmarks(),
      ]);
      setResumes(resumesData);
      setBookmarks(bookmarksData);
    } catch (error) {
      console.error("Failed to fetch data:", error);
      toast({
        title: "Error loading data",
        description:
          error instanceof Error ? error.message : "Failed to load resumes",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (mounted) {
      fetchData();
    }
  }, [mounted, fetchData]);

  const handleEdit = useCallback((resume: ResumeData) => {
    setEditingResume(resume);
    setShowEditModal(true);
  }, []);

  const handleAnalysis = useCallback(
    async (resume: ResumeData, force: boolean = false) => {
      setAnalyzingResume(resume);
      try {
        const result = await analyzeResume(resume.id, force);
        setAnalysisResult(result);
        setLastAnalyzedResume(resume);
        await fetchData(); // Refresh data to get updated tips
      } catch (error) {
        toast({
          title: "Analysis failed",
          description:
            error instanceof Error ? error.message : "Failed to analyze resume",
          variant: "destructive",
        });
      } finally {
        setAnalyzingResume(null);
      }
    },
    [fetchData]
  );

  const dismissAnalysis = useCallback(() => {
    setAnalysisResult(null);
    setLastAnalyzedResume(null);
  }, []);

  const handleAnalyzeAgain = useCallback(async () => {
    if (!lastAnalyzedResume) return;

    await handleAnalysis(lastAnalyzedResume, true);
  }, [lastAnalyzedResume, handleAnalysis]);

  const handleRefresh = useCallback(() => {
    fetchData();
  }, [fetchData]);

  if (!mounted) {
    return null;
  }

  return (
    <div className="space-y-8 px-4 md:px-8 lg:px-16 xl:px-24 max-w-7xl mx-auto">
      {/* Header */}
      <div className="space-y-3">
        <h1 className="text-3xl font-bold tracking-tight text-text-primary dark:text-[#e4e6eb]">
          Resume Tips
        </h1>
        <p className="text-text-secondary dark:text-[#b0b3b8]">
          Upload and manage your resumes. Get AI-powered tips to optimize for
          specific jobs. <b>Cost: 5 credits/analysis.</b>
        </p>
      </div>

      {/* Controls Bar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isLoading}
          >
            <RefreshCw
              className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>
        </div>

        <div className="flex items-center gap-2">
          {/* View Toggle */}
          <div className="flex items-center border rounded-lg p-1 bg-muted/50">
            <Button
              variant={viewMode === "grid" ? "secondary" : "ghost"}
              size="sm"
              className="h-8 px-3"
              onClick={() => setViewMode("grid")}
            >
              <Grid3X3 className="h-4 w-4" />
            </Button>
            <Button
              variant={viewMode === "list" ? "secondary" : "ghost"}
              size="sm"
              className="h-8 px-3"
              onClick={() => setViewMode("list")}
            >
              <List className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Analysis Result Card */}
      {analysisResult && lastAnalyzedResume && (
        <Card className="max-w-4xl">
          <ResumeAnalysisCard
            analysis={analysisResult}
            resume={lastAnalyzedResume}
            onDismiss={dismissAnalysis}
            onAnalyzeAgain={handleAnalyzeAgain}
            isAnalyzing={analyzingResume?.id === lastAnalyzedResume.id}
          />
        </Card>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      )}

      {/* Content */}
      {!isLoading && (
        <>
          {viewMode === "grid" ? (
            /* Grid View */
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {/* Upload Card */}
              <Card
                className="overflow-hidden cursor-pointer hover:shadow-lg transition-all border-dashed border-2 hover:border-primary/50 group"
                onClick={() => setShowUploadModal(true)}
              >
                <div className="aspect-[3/4] flex flex-col items-center justify-center text-muted-foreground group-hover:text-primary transition-colors">
                  <div className="w-16 h-16 rounded-full bg-muted group-hover:bg-primary/10 flex items-center justify-center mb-4 transition-colors">
                    <Upload className="h-8 w-8" />
                  </div>
                  <span className="font-medium text-foreground">
                    Create new resume
                  </span>
                  <span className="text-sm mt-1">Upload PDF or DOCX</span>
                </div>
              </Card>

              {/* Resume Cards */}
              {resumes.map((resume) => (
                <ResumeCard
                  key={resume.id}
                  resume={resume}
                  onEdit={handleEdit}
                  onAnalyze={handleAnalysis}
                  onRefresh={handleRefresh}
                  viewMode="grid"
                  isAnalyzing={analyzingResume?.id === resume.id}
                />
              ))}
            </div>
          ) : (
            /* List View */
            <div className="space-y-4">
              {/* Upload Card */}
              <Card
                className="cursor-pointer hover:shadow-md transition-all border-dashed border-2 hover:border-primary/50"
                onClick={() => setShowUploadModal(true)}
              >
                <CardContent className="p-4">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-lg bg-muted flex items-center justify-center">
                      <Upload className="h-6 w-6 text-muted-foreground" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-foreground">
                        Upload new resume
                      </h3>
                      <p className="text-sm text-muted-foreground">
                        PDF or DOCX (max 20MB)
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Resume Cards */}
              {resumes.map((resume) => (
                <ResumeCard
                  key={resume.id}
                  resume={resume}
                  onEdit={handleEdit}
                  onAnalyze={handleAnalysis}
                  onRefresh={handleRefresh}
                  viewMode="list"
                  isAnalyzing={analyzingResume?.id === resume.id}
                />
              ))}
            </div>
          )}

          {/* Empty State */}
          {resumes.length === 0 && (
            <Card className="p-12 text-center">
              <FileText className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-xl font-semibold text-foreground mb-2">
                No resumes yet
              </h3>
              <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                Upload your first resume to get started. Our AI will analyze it
                and provide personalized tips to help you land your dream job.
              </p>
              <Button onClick={() => setShowUploadModal(true)}>
                <Upload className="mr-2 h-4 w-4" />
                Upload Resume
              </Button>
            </Card>
          )}
        </>
      )}

      {/* Upload Modal */}
      <ResumeUploadModal
        open={showUploadModal}
        onOpenChange={setShowUploadModal}
        bookmarks={bookmarks}
        onSuccess={handleRefresh}
      />

      {/* Edit Modal */}
      <ResumeEditModal
        open={showEditModal}
        onOpenChange={setShowEditModal}
        resume={editingResume}
        bookmarks={bookmarks}
        onSuccess={handleRefresh}
      />
    </div>
  );
}
