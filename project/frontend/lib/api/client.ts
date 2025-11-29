/**
 * API Client for Backend Communication
 * Handles authenticated requests to the FastAPI backend
 */

import { createClient } from "@/lib/supabase/client"

// Performance monitoring helper
const logApiCall = (endpoint: string, startTime: number, success: boolean, error?: string) => {
  const duration = performance.now() - startTime
  const status = success ? 'SUCCESS' : 'FAILED'
  console.log(`[API] ${endpoint} - ${status} (${duration.toFixed(2)}ms)`, error ? { error } : '')
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export type ApplicationStatus = 
  | "interested" 
  | "applied" 
  | "interviewing" 
  | "interviewed_passed" 
  | "interviewed_failed"

export interface ExtractedJobData {
  company: string | null
  location: string | null
  industry: string | null
}

export interface JobBookmarkData {
  bookmark_id: string
  user_id: string
  title: string
  company: string
  location: string | null
  source: string
  source_url: string | null
  description: string | null
  application_status: ApplicationStatus
  created_at: string
  job_industry_id: number | null
  // Analysis data
  is_authentic: boolean | null
  confidence_score: number | null
  analysis_evidence: string | null
  analysis_type: string | null
}

export interface JobAnalysisData {
  analysis_id: string
  user_id: string
  job_bookmark_id: string | null
  confidence_score: number | null
  is_authentic: boolean | null
  evidence: string | null
  analysis_type: string
  credits_used: number
  created_at: string
  extracted_data: ExtractedJobData | null
}

export interface JobUrlSearchResponse {
  bookmarked: boolean
  already_bookmarked: boolean
  bookmark_id: string | null
  job_data: JobBookmarkData | null
  analysis: JobAnalysisData
}

export interface DashboardStats {
  job_bookmarks: number
  in_interview: number
  failed_interview: number
  avg_match_score: number | null
  credits_remaining: number
  potential_jobs: number
  job_bookmarks_change: number | null
  in_interview_change: number | null
  avg_match_score_change: number | null
  potential_jobs_change: number | null
}

export interface ApiError {
  detail: string | { error?: string; message?: string; is_safe?: boolean; threat_types?: string[] }
}

/**
 * Get authentication token from Supabase session
 */
async function getAuthToken(): Promise<string | null> {
  const supabase = createClient()
  const {
    data: { session },
  } = await supabase.auth.getSession()
  
  return session?.access_token || null
}

/**
 * Make authenticated API request
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = await getAuthToken()
  
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  }
  
  // Merge existing headers if they exist
  if (options.headers) {
    const existingHeaders = options.headers as Record<string, string>
    Object.assign(headers, existingHeaders)
  }
  
  if (token) {
    headers["Authorization"] = `Bearer ${token}`
  }
  
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  })
  
  if (!response.ok) {
    const errorData: ApiError = await response.json().catch(() => ({
      detail: `HTTP ${response.status}: ${response.statusText}`,
    }))
    
    // Handle different error formats
    let errorMessage = "An error occurred"
    if (typeof errorData.detail === "string") {
      errorMessage = errorData.detail
    } else if (errorData.detail?.message) {
      errorMessage = errorData.detail.message
    } else if (errorData.detail?.error) {
      errorMessage = errorData.detail.error
    }
    
    throw new Error(errorMessage)
  }
  
  return response.json()
}

/**
 * Search job by URL
 */
export async function searchJobByUrl(url: string): Promise<JobUrlSearchResponse> {
  return apiRequest<JobUrlSearchResponse>("/api/v1/jobs/search-by-url", {
    method: "POST",
    body: JSON.stringify({ url }),
  })
}

/**
 * Submit manual job information
 */
export async function submitManualJob(jobData: {
  job_title: string
  company: string
  location?: string
  industry?: string
  source?: string
  description: string
}): Promise<JobUrlSearchResponse> {
  return apiRequest<JobUrlSearchResponse>("/api/v1/jobs/submit-manual", {
    method: "POST",
    body: JSON.stringify(jobData),
  })
}

/**
 * Get dashboard statistics for the current user
 */
export async function getDashboardStats(): Promise<DashboardStats> {
  const startTime = performance.now()
  const endpoint = '/api/v1/users/dashboard/stats'

  try {
    const supabase = createClient()
    const { data: { session } } = await supabase.auth.getSession()

    if (!session?.access_token) {
      throw new Error("No authentication token found")
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${session.access_token}`
      }
    })


  if (!response.ok) {
    // Handle different error formats
    let errorMessage = "Failed to fetch dashboard statistics"
    try {
      const errorData = await response.json()
      if (typeof errorData.detail === "string") {
        errorMessage = errorData.detail
      } else if (errorData.detail?.message) {
        errorMessage = errorData.detail.message
      } else if (errorData.detail?.error) {
        errorMessage = errorData.detail.error
      }
    } catch {
      errorMessage = `HTTP ${response.status}: ${response.statusText}`
    }

    throw new Error(errorMessage)
  }

  const data = await response.json()
  logApiCall(endpoint, startTime, true)
  return data
  } catch (error) {
    logApiCall(endpoint, startTime, false, error instanceof Error ? error.message : 'Unknown error')
    throw error
  }
}

/**
 * Get user bookmarks with analysis data
 */
export async function getBookmarks(): Promise<JobBookmarkData[]> {
  const startTime = performance.now()
  const endpoint = '/api/v1/jobs/bookmarks'

  try {
    const supabase = createClient()
    const { data: { session } } = await supabase.auth.getSession()

    if (!session?.access_token) {
      throw new Error("No authentication token found")
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${session.access_token}`
    }
  })

  if (!response.ok) {
    // Handle different error formats
    let errorMessage = "Failed to fetch bookmarks"
    try {
      const errorData = await response.json()
      if (typeof errorData.detail === "string") {
        errorMessage = errorData.detail
      } else if (errorData.detail?.message) {
        errorMessage = errorData.detail.message
      } else if (errorData.detail?.error) {
        errorMessage = errorData.detail.error
      }
    } catch {
      errorMessage = `HTTP ${response.status}: ${response.statusText}`
    }

    throw new Error(errorMessage)
  }

  const data = await response.json()
  logApiCall(endpoint, startTime, true)
  return data
  } catch (error) {
    logApiCall(endpoint, startTime, false, error instanceof Error ? error.message : 'Unknown error')
    throw error
  }
}

/**
 * Get detailed bookmark information
 */
export async function getBookmarkDetail(bookmarkId: string): Promise<JobBookmarkData> {
  const supabase = createClient()
  const { data: { session } } = await supabase.auth.getSession()

  if (!session?.access_token) {
    throw new Error("No authentication token found")
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/bookmarks/${bookmarkId}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${session.access_token}`
    }
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(errorData.detail || 'Failed to fetch bookmark details')
  }

  return response.json()
}

/**
 * Update a bookmark
 */
export async function updateBookmark(
  bookmarkId: string,
  updates: Partial<JobBookmarkData>
): Promise<JobBookmarkData> {
  const supabase = createClient()
  const { data: { session } } = await supabase.auth.getSession()

  if (!session?.access_token) {
    throw new Error("No authentication token found")
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/bookmarks/${bookmarkId}`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${session.access_token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(updates)
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(errorData.detail || 'Failed to update bookmark')
  }

  return response.json()
}

/**
 * Delete a bookmark
 */
export async function deleteBookmark(bookmarkId: string): Promise<void> {
  const supabase = createClient()
  const { data: { session } } = await supabase.auth.getSession()

  if (!session?.access_token) {
    throw new Error("No authentication token found")
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/bookmarks/${bookmarkId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${session.access_token}`
    }
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(errorData.detail || 'Failed to delete bookmark')
  }
}

/**
 * Upload and analyze job document
 */
export async function uploadJobDocument(file: File): Promise<JobUrlSearchResponse> {
  const supabase = createClient()
  const { data: { session } } = await supabase.auth.getSession()

  if (!session?.access_token) {
    throw new Error("No authentication token found")
  }

  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/upload-job-document`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${session.access_token}`
    },
    body: formData
  })

  if (!response.ok) {
    // Handle different error formats
    let errorMessage = "Document upload failed"
    try {
      const errorData = await response.json()
      if (typeof errorData.detail === "string") {
        errorMessage = errorData.detail
      } else if (errorData.detail?.message) {
        errorMessage = errorData.detail.message
      } else if (errorData.detail?.error) {
        errorMessage = errorData.detail.error
      }
    } catch {
      errorMessage = `HTTP ${response.status}: ${response.statusText}`
    }

    throw new Error(errorMessage)
  }

  return response.json()
}

// ============================================================================
// Resume Types and API Functions
// ============================================================================

export type ExperienceLevel = "junior" | "mid_senior" | "director" | "executive"

export interface ResumeData {
  id: string
  filename: string
  size: number
  uploaded_at: string
  object_id: string
  user_id: string
  resume_name: string | null
  experience: ExperienceLevel | null
  targeted_job_bookmark_id: string | null
  match_score: number | null
  recommended_tips: string | null
  targeted_job_title: string | null
  targeted_job_company: string | null
}

export interface ResumeCreateData {
  resume_name: string
  experience: ExperienceLevel
  targeted_job_bookmark_id?: string | null
}

export interface ResumeUpdateData {
  resume_name?: string
  experience?: ExperienceLevel
  targeted_job_bookmark_id?: string | null
}

export interface ResumeAnalysisResult {
  resume_id: string
  match_score: number | null
  recommended_tips: string
  targeted_job_title: string | null
  targeted_job_company: string | null
  credits_used: number
  last_analyzed_at: string | null
}

/**
 * Get all resumes for the current user
 */
export async function getResumes(): Promise<ResumeData[]> {
  const supabase = createClient()
  const { data: { session } } = await supabase.auth.getSession()

  if (!session?.access_token) {
    throw new Error("No authentication token found")
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/resumes/`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${session.access_token}`
    }
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(errorData.detail || 'Failed to fetch resumes')
  }

  return response.json()
}

/**
 * Get a specific resume by ID
 */
export async function getResume(resumeId: string): Promise<ResumeData> {
  const supabase = createClient()
  const { data: { session } } = await supabase.auth.getSession()

  if (!session?.access_token) {
    throw new Error("No authentication token found")
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/resumes/${resumeId}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${session.access_token}`
    }
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(errorData.detail || 'Failed to fetch resume')
  }

  return response.json()
}

/**
 * Create a new resume (upload file with metadata)
 */
export async function createResume(
  file: File,
  metadata: ResumeCreateData
): Promise<ResumeData> {
  const supabase = createClient()
  const { data: { session } } = await supabase.auth.getSession()

  if (!session?.access_token) {
    throw new Error("No authentication token found")
  }

  const formData = new FormData()
  formData.append('file', file)
  formData.append('resume_name', metadata.resume_name)
  formData.append('experience', metadata.experience)
  if (metadata.targeted_job_bookmark_id) {
    formData.append('targeted_job_bookmark_id', metadata.targeted_job_bookmark_id)
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/resumes/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${session.access_token}`
    },
    body: formData
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(errorData.detail || 'Failed to create resume')
  }

  return response.json()
}

/**
 * Update resume metadata
 */
export async function updateResume(
  resumeId: string,
  updates: ResumeUpdateData
): Promise<ResumeData> {
  const supabase = createClient()
  const { data: { session } } = await supabase.auth.getSession()

  if (!session?.access_token) {
    throw new Error("No authentication token found")
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/resumes/${resumeId}`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${session.access_token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(updates)
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(errorData.detail || 'Failed to update resume')
  }

  return response.json()
}

/**
 * Delete a resume
 */
export async function deleteResume(resumeId: string): Promise<void> {
  const supabase = createClient()
  const { data: { session } } = await supabase.auth.getSession()

  if (!session?.access_token) {
    throw new Error("No authentication token found")
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/resumes/${resumeId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${session.access_token}`
    }
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(errorData.detail || 'Failed to delete resume')
  }
}

/**
 * Duplicate a resume
 */
export async function duplicateResume(resumeId: string): Promise<ResumeData> {
  const supabase = createClient()
  const { data: { session } } = await supabase.auth.getSession()

  if (!session?.access_token) {
    throw new Error("No authentication token found")
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/resumes/${resumeId}/duplicate`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${session.access_token}`
    }
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(errorData.detail || 'Failed to duplicate resume')
  }

  return response.json()
}

/**
 * Analyze resume with Gemini AI
 */
export async function analyzeResume(resumeId: string, force: boolean = false): Promise<ResumeAnalysisResult> {
  const supabase = createClient()
  const { data: { session } } = await supabase.auth.getSession()

  if (!session?.access_token) {
    throw new Error("No authentication token found")
  }

  const url = new URL(`${API_BASE_URL}/api/v1/resumes/${resumeId}/analyze`)
  if (force) {
    url.searchParams.set('force', 'true')
  }

  const response = await fetch(url.toString(), {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${session.access_token}`
    }
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(errorData.detail || 'Failed to analyze resume')
  }

  return response.json()
}

/**
 * Get signed URL for resume preview
 */
export async function getResumePreviewUrl(resumeId: string): Promise<string> {
  const supabase = createClient()
  const { data: { session } } = await supabase.auth.getSession()

  if (!session?.access_token) {
    throw new Error("No authentication token found")
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/resumes/${resumeId}/preview-url`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${session.access_token}`
    }
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(errorData.detail || 'Failed to get preview URL')
  }

  const data = await response.json()
  return data.preview_url
}

/**
 * Get signed URL for resume download
 */
export async function getResumeDownloadUrl(resumeId: string): Promise<string> {
  const supabase = createClient()
  const { data: { session } } = await supabase.auth.getSession()

  if (!session?.access_token) {
    throw new Error("No authentication token found")
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/resumes/${resumeId}/download-url`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${session.access_token}`
    }
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(errorData.detail || 'Failed to get download URL')
  }

  const data = await response.json()
  return data.download_url
}


