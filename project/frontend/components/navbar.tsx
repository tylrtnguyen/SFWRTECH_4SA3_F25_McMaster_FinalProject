"use client"

import { Bell, Moon, Sun, User, LogOut } from "lucide-react"
import { useTheme } from "next-themes"
import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { createClient } from "@/lib/supabase/client"
import { useUser } from "@/lib/contexts/user-context"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"

export function Navbar() {
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)
  const [notificationsOpen, setNotificationsOpen] = useState(false)
  const { userData } = useUser()
  const router = useRouter()
  const supabase = createClient()

  // Fake notifications data
  const notifications = [
    {
      id: 1,
      title: "Job Analysis Complete",
      message: "Your job application for Senior Software Engineer at Google has been analyzed.",
      time: "2 minutes ago",
      type: "analysis",
      unread: true,
    },
    {
      id: 2,
      title: "New Job Match Found",
      message: "We found a new job that matches your resume: Product Manager at Meta.",
      time: "1 hour ago",
      type: "match",
      unread: true,
    },
    {
      id: 3,
      title: "Credits Low",
      message: "You have 2 credits remaining. Consider purchasing more credits.",
      time: "3 hours ago",
      type: "warning",
      unread: false,
    },
    {
      id: 4,
      title: "Profile Updated",
      message: "Your profile information has been successfully updated.",
      time: "1 day ago",
      type: "success",
      unread: false,
    },
    {
      id: 5,
      title: "Weekly Summary",
      message: "This week you applied to 3 jobs and received 2 interview callbacks.",
      time: "2 days ago",
      type: "summary",
      unread: false,
    },
  ]

  useEffect(() => {
    setMounted(true)
  }, [])

  const handleLogout = async () => {
    // Sign out with scope: 'local' to clear local session and cookies
    const { error } = await supabase.auth.signOut({ scope: 'local' })
    
    if (error) {
      console.error("Error signing out:", error)
    }
    
    // Force a full page reload to ensure cookies are cleared
    // This ensures middleware can properly detect the logout
    window.location.href = "/login"
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border-default dark:border-[#3a3f4b] bg-bg-secondary dark:bg-[#22262e]">
      <div className="flex h-16 items-center justify-between px-6">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded bg-primary-600 dark:bg-primary-400 text-primary-foreground font-bold text-lg">
            JT
          </div>
          <span className="text-xl font-bold text-primary-600 dark:text-primary-400">JobTrust</span>
        </div>

        <div className="flex items-center gap-2">
          {/* Notifications */}
          <Button
            variant="ghost"
            size="icon"
            className="relative"
            onClick={() => setNotificationsOpen(true)}
          >
            <Bell className="h-5 w-5" />
            <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-red-500" />
          </Button>

          {/* Theme Toggle */}
          {mounted && (
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            >
              {theme === "dark" ? (
                <Sun className="h-5 w-5" />
              ) : (
                <Moon className="h-5 w-5" />
              )}
            </Button>
          )}

          {/* User Settings */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="relative h-10 w-10 rounded-full">
                <Avatar className="h-10 w-10">
                  <AvatarImage src="" alt="User" />
                  <AvatarFallback className="bg-primary text-primary-foreground">
                    <User className="h-5 w-5" />
                  </AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56" align="end" forceMount>
              <DropdownMenuLabel className="font-normal">
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium leading-none">
                    {userData?.firstName && userData?.lastName
                      ? `${userData.firstName} ${userData.lastName}`
                      : userData?.firstName || userData?.lastName || "User"
                    }
                  </p>
                  <p className="text-xs leading-none text-muted-foreground">
                    {userData?.email || "user@example.com"}
                  </p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => router.push("/dashboard/profile")}>
                <User className="mr-2 h-4 w-4" />
                <span>Profile</span>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout}>
                <LogOut className="mr-2 h-4 w-4" />
                <span>Log out</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Notifications Modal */}
      <Dialog open={notificationsOpen} onOpenChange={setNotificationsOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Notifications</DialogTitle>
          </DialogHeader>
          <ScrollArea className="max-h-96">
            <div className="space-y-4">
              {notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`p-3 rounded-lg border ${
                    notification.unread
                      ? "bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800"
                      : "bg-background border-border"
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="text-sm font-medium">{notification.title}</h4>
                        {notification.unread && (
                          <Badge variant="secondary" className="text-xs px-1 py-0">
                            New
                          </Badge>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground mb-1">
                        {notification.message}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {notification.time}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </DialogContent>
      </Dialog>
    </header>
  )
}

