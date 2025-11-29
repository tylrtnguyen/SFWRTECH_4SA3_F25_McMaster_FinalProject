import { createBrowserClient } from '@supabase/ssr'
import type { Database } from './types'

let supabaseClient: ReturnType<typeof createBrowserClient<Database>> | null = null

export function createClient(): ReturnType<typeof createBrowserClient<Database>> {
  // Return cached instance if it exists
  if (supabaseClient) {
    return supabaseClient
  }

  // Create new instance and cache it
  supabaseClient = createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )

  return supabaseClient
}

