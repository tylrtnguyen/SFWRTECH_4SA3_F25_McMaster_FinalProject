"use client"

import React, { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react'
import { createClient } from '@/lib/supabase/client'

interface UserData {
  firstName?: string
  lastName?: string
  email?: string
  credits?: number
  isLoading: boolean
  error?: string
}

interface UserContextType {
  userData: UserData | null
  refetchUserData: () => Promise<void>
  updateUserData: (updates: Partial<UserData>) => void
}

const UserContext = createContext<UserContextType | undefined>(undefined)

export function useUser() {
  const context = useContext(UserContext)
  if (context === undefined) {
    throw new Error('useUser must be used within a UserProvider')
  }
  return context
}

interface UserProviderProps {
  children: ReactNode
}

export function UserProvider({ children }: UserProviderProps) {
  const [userData, setUserData] = useState<UserData | null>({
    isLoading: true
  })

  const supabase = createClient()

  const fetchUserData = useCallback(async () => {
    try {
      setUserData(prev => prev ? { ...prev, isLoading: true, error: undefined } : { isLoading: true })

      const { data: { user } } = await supabase.auth.getUser()

      if (!user) {
        setUserData(null)
        return
      }

      // Get user details from users table
      const { data: userDetails, error: userError } = await supabase
        .from("users")
        .select("first_name, last_name, credits")
        .eq("user_id", user.id)
        .single()

      if (userError) {
        throw userError
      }

      setUserData({
        firstName: userDetails?.first_name,
        lastName: userDetails?.last_name,
        email: user.email,
        credits: userDetails?.credits,
        isLoading: false
      })
    } catch (error) {
      console.error("Error fetching user data:", error)
      setUserData(prev => prev ? {
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to fetch user data'
      } : {
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to fetch user data'
      })
    }
  }, [supabase])

  const updateUserData = useCallback((updates: Partial<UserData>) => {
    setUserData(prev => {
      if (!prev) return prev
      return { ...prev, ...updates }
    })
  }, [])

  const refetchUserData = useCallback(async () => {
    await fetchUserData()
  }, [fetchUserData])

  useEffect(() => {
    fetchUserData()

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
      if (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED') {
        await fetchUserData()
      } else if (event === 'SIGNED_OUT') {
        setUserData(null)
      }
    })

    return () => {
      subscription.unsubscribe()
    }
  }, [fetchUserData, supabase])

  const value: UserContextType = {
    userData,
    refetchUserData,
    updateUserData
  }

  return (
    <UserContext.Provider value={value}>
      {children}
    </UserContext.Provider>
  )
}
