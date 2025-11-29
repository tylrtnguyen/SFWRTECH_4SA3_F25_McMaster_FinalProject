import { createClient } from "@/lib/supabase/client"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export interface Industry {
  id: number
  description: string
  created_at: string
}

// Cache for industries to avoid repeated API calls
let industriesCache: Industry[] | null = null
let cacheTimestamp: number | null = null
const CACHE_DURATION = 5 * 60 * 1000 // 5 minutes

export async function getIndustries(): Promise<string[]> {
  try {
    // Check cache first
    const now = Date.now()
    if (industriesCache && cacheTimestamp && (now - cacheTimestamp) < CACHE_DURATION) {
      return industriesCache.map(ind => ind.description)
    }

    // Fetch from API
    const token = await getAuthToken()
    const response = await fetch(`${API_BASE_URL}/api/v1/jobs/industries`, {
      headers: {
        "Content-Type": "application/json",
        ...(token ? { "Authorization": `Bearer ${token}` } : {}),
      },
    })

    if (!response.ok) {
      throw new Error(`Failed to fetch industries: ${response.status}`)
    }

    const industries: Industry[] = await response.json()
    industriesCache = industries
    cacheTimestamp = now

    return industries.map(ind => ind.description).sort()
  } catch (error) {
    console.error("Error fetching industries from API:", error)
    // Fallback to basic defaults if API fails
    return [
  "Technology",
  "Healthcare",
  "Finance",
  "Education",
  "Manufacturing",
  "Retail",
  "Consulting",
      "Other"
    ]
  }
}

export async function addIndustry(industry: string): Promise<void> {
  const normalized = industry.trim()
  if (!normalized) return

  try {
    const token = await getAuthToken()
    const response = await fetch(`${API_BASE_URL}/api/v1/jobs/industries`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { "Authorization": `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(normalized),
    })

    if (!response.ok) {
      throw new Error(`Failed to add industry: ${response.status}`)
    }

    // Clear cache to force refresh on next fetch
    industriesCache = null
    cacheTimestamp = null
  } catch (error) {
    console.error("Error adding industry via API:", error)
    throw error
  }
}

export function removeIndustry(industry: string): void {
  // Industries are now managed server-side, so removal is not supported from frontend
  // This function is kept for compatibility but does nothing
  console.warn("Industry removal is not supported from frontend")
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

