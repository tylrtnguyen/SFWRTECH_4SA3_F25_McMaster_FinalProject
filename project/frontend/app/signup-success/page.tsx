"use client"

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
import { CheckCircle2 } from "lucide-react"

export default function SignupSuccessPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-bg-primary dark:bg-[#1a1d23] px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <div className="flex justify-center mb-4">
            <CheckCircle2 className="h-16 w-16 text-success-600 dark:text-success-400" />
          </div>
          <CardTitle className="text-2xl font-bold text-text-primary dark:text-[#e4e6eb]">
            Congratulations!
          </CardTitle>
          <CardDescription className="text-text-secondary dark:text-[#b0b3b8]">
            Your account has been created successfully.
          </CardDescription>
        </CardHeader>
        <CardContent className="text-center">
          <p className="text-text-secondary dark:text-[#b0b3b8]">
            You can now sign in to your account and start using JobTrust.
          </p>
        </CardContent>
        <CardFooter className="flex justify-center">
          <Link href="/login" className="w-full">
            <Button className="w-full">Go to Login</Button>
          </Link>
        </CardFooter>
      </Card>
    </div>
  )
}

