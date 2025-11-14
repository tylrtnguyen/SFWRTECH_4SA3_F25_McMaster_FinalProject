"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  FileText,
  Calculator,
  FileCheck,
  Bookmark,
  Settings,
  User,
  LayoutDashboard,
  ChevronLeft,
  ChevronRight,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Analyze Job", href: "/dashboard/analyze", icon: FileText },
  { name: "Match Score", href: "/dashboard/match", icon: Calculator },
  { name: "Resume Tips", href: "/dashboard/resume", icon: FileCheck },
  { name: "Bookmarks", href: "/dashboard/bookmarks", icon: Bookmark },
  { name: "Settings", href: "/dashboard/settings", icon: Settings },
  { name: "Profile", href: "/dashboard/profile", icon: User },
]

export function Sidebar() {
  const pathname = usePathname()
  const [isCollapsed, setIsCollapsed] = useState(false)

  return (
    <div
      className={cn(
        "flex h-full flex-col border-r border-border-default bg-bg-secondary dark:border-[#3a3f4b] dark:bg-[#22262e] transition-all duration-300",
        isCollapsed ? "w-16" : "w-64"
      )}
    >
      <div className="flex h-16 items-center justify-between border-b border-border-default dark:border-[#3a3f4b] px-4">
        {!isCollapsed && (
          <h2 className="text-xl font-bold text-primary-600 dark:text-primary-400">
            JobTrust
          </h2>
        )}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="ml-auto h-8 w-8"
        >
          {isCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </Button>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.name}
              href={item.href}
              title={isCollapsed ? item.name : undefined}
              className={cn(
                "flex items-center rounded-lg px-3 py-4 text-sm font-medium transition-colors",
                isCollapsed ? "justify-center" : "gap-3",
                isActive
                  ? "bg-primary-600 dark:bg-primary-400 text-primary-foreground"
                  : "text-text-secondary dark:text-[#b0b3b8] hover:bg-bg-secondary dark:hover:bg-[#22262e] hover:text-text-primary dark:hover:text-[#e4e6eb]"
              )}
            >
              <item.icon 
                className={cn(
                  isCollapsed ? "h-6 w-6 flex-shrink-0" : "h-5 w-5 flex-shrink-0"
                )} 
              />
              {!isCollapsed && <span>{item.name}</span>}
            </Link>
          )
        })}
      </nav>
    </div>
  )
}

