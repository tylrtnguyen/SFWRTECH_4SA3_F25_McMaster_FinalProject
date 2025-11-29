"use client"

import { Suspense } from "react"
import { useSearchParams } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

function UnauthorizedContent() {
  const searchParams = useSearchParams()
  const redirectTo = searchParams.get("redirectTo") || "/dashboard"

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg-primary dark:bg-[#1a1d23] px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <CardTitle className="text-4xl font-bold text-text-primary dark:text-[#e4e6eb]">
            401
          </CardTitle>
          <CardDescription className="text-lg text-text-secondary dark:text-[#b0b3b8]">
            Unauthorized Access
          </CardDescription>
        </CardHeader>
        <CardContent className="text-center">
          <p className="text-text-secondary dark:text-[#b0b3b8]">
            You need to be logged in to access this page. Please sign in to continue.
          </p>
        </CardContent>
        <CardFooter className="flex justify-center">
          <Link href={`/login?redirectTo=${encodeURIComponent(redirectTo)}`}>
            <Button>Go to Login</Button>
          </Link>
        </CardFooter>
      </Card>
    </div>
  )
}

export default function UnauthorizedPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center bg-bg-primary dark:bg-[#1a1d23] px-4">
        <Card className="w-full max-w-md">
          <CardHeader className="space-y-1 text-center">
            <CardTitle className="text-4xl font-bold text-text-primary dark:text-[#e4e6eb]">
              401
            </CardTitle>
            <CardDescription className="text-lg text-text-secondary dark:text-[#b0b3b8]">
              Unauthorized Access
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center">
            <p className="text-text-secondary dark:text-[#b0b3b8]">
              Loading...
            </p>
          </CardContent>
        </Card>
      </div>
    }>
      <UnauthorizedContent />
    </Suspense>
  )
}
