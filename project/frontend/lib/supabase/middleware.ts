import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

export async function updateSession(request: NextRequest) {
  let supabaseResponse = NextResponse.next({
    request,
  })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(cookiesToSet: Array<{ name: string; value: string; options?: any }>) {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value))
          supabaseResponse = NextResponse.next({
            request,
          })
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          )
        },
      },
    } as any
  )

  // Refresh session if expired - required for Server Components
  // This ensures cookies are properly read and synced
  // The getSession() call refreshes the session from cookies
  const {
    data: { session },
  } = await supabase.auth.getSession()
  
  // Get user from the refreshed session
  const {
    data: { user },
    error: authError,
  } = await supabase.auth.getUser()

  // Protect /dashboard routes
//   if (request.nextUrl.pathname.startsWith('/dashboard')) {
//     if (!user) {
//       // No user found, redirect to 401 unauthorized page
//       const url = request.nextUrl.clone()
//       url.pathname = '/401'
//       url.searchParams.set('redirectTo', request.nextUrl.pathname)
//       return NextResponse.redirect(url)
//     }
//   }

  // Allow public access to auth pages and error pages
  const publicPaths = ['/login', '/signup', '/signup-success', '/401', '/not-found']
  if (publicPaths.includes(request.nextUrl.pathname)) {
    return supabaseResponse
  }

  // Redirect authenticated users away from login/signup pages
  // But only if they're not in the middle of a redirect flow
  if (user && (request.nextUrl.pathname === '/login' || request.nextUrl.pathname === '/signup')) {
    // Check if there's a redirectTo parameter - if so, allow the login page to handle it
    const redirectTo = request.nextUrl.searchParams.get('redirectTo')
    if (!redirectTo) {
      const url = request.nextUrl.clone()
      url.pathname = '/dashboard'
      return NextResponse.redirect(url)
    }
  }

  return supabaseResponse
}

