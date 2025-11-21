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

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-bg-primary dark:bg-[#1a1d23] px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <CardTitle className="text-4xl font-bold text-text-primary dark:text-[#e4e6eb]">
            404
          </CardTitle>
          <CardDescription className="text-lg text-text-secondary dark:text-[#b0b3b8]">
            Page Not Found
          </CardDescription>
        </CardHeader>
        <CardContent className="text-center">
          <p className="text-text-secondary dark:text-[#b0b3b8]">
            The page you're looking for doesn't exist or has been moved.
          </p>
        </CardContent>
        <CardFooter className="flex justify-center gap-4">
          <Link href="/dashboard">
            <Button>Go to Dashboard</Button>
          </Link>
          <Link href="/">
            <Button variant="outline">Go Home</Button>
          </Link>
        </CardFooter>
      </Card>
    </div>
  )
}

