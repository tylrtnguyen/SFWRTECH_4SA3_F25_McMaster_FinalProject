const STORAGE_KEY = "jobtrust_industries"

const DEFAULT_INDUSTRIES = [
  "Technology",
  "Healthcare",
  "Finance",
  "Education",
  "Manufacturing",
  "Retail",
  "Hospitality",
  "Construction",
  "Transportation",
  "Energy",
  "Media & Entertainment",
  "Real Estate",
  "Consulting",
  "Government",
  "Non-profit",
]

export function getIndustries(): string[] {
  if (typeof window === "undefined") {
    return DEFAULT_INDUSTRIES
  }

  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      const parsed = JSON.parse(stored)
      return Array.isArray(parsed) ? parsed : DEFAULT_INDUSTRIES
    }
  } catch (error) {
    console.error("Error reading industries from localStorage:", error)
  }

  // Initialize with default industries if nothing exists
  localStorage.setItem(STORAGE_KEY, JSON.stringify(DEFAULT_INDUSTRIES))
  return DEFAULT_INDUSTRIES
}

export function addIndustry(industry: string): void {
  if (typeof window === "undefined") return

  const industries = getIndustries()
  const normalized = industry.trim()

  if (normalized && !industries.includes(normalized)) {
    const updated = [...industries, normalized].sort()
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
    } catch (error) {
      console.error("Error saving industry to localStorage:", error)
    }
  }
}

export function removeIndustry(industry: string): void {
  if (typeof window === "undefined") return

  const industries = getIndustries()
  const updated = industries.filter((ind) => ind !== industry)
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
  } catch (error) {
    console.error("Error removing industry from localStorage:", error)
  }
}

