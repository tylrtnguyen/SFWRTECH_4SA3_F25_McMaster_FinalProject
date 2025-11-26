/**
 * API Client for Backend Communication
 * Handles authenticated requests to the FastAPI backend
 */

import { createClient } from "@/lib/supabase/client"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export interface JobUrlSearchResponse {
  bookmark_id: string
  job_data: {
    bookmark_id: string
    user_id: string
    title: string
    company: string
    location: string | null
    source: string
    source_url: string | null
    description: string | null
    created_at: string
  }
  analysis: {
    analysis_id: string
    user_id: string
    job_bookmark_id: string
    confidence_score: number | null
    is_authentic: boolean | null
    evidence: string | null
    analysis_type: string
    credits_used: number
    created_at: string
  }
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
  
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...options.headers,
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


