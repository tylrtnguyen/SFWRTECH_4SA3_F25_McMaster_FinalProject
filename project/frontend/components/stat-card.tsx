import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"

interface StatCardProps {
  title: string
  value: string | number
  description?: string
  icon: LucideIcon
  trend?: {
    value: string
    isPositive: boolean
    isPercentage?: boolean
  }
  className?: string
}

export function StatCard({
  title,
  value,
  description,
  icon: Icon,
  trend,
  className,
}: StatCardProps) {
  return (
    <Card className={cn("hover:shadow-md transition-shadow", className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-text-primary dark:text-[#e4e6eb]">{title}</CardTitle>
        <Icon className="h-6 w-6 text-text-tertiary dark:text-[#8a8d91]" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold text-text-primary dark:text-[#e4e6eb]">{value}</div>
        {description && (
          <CardDescription className="mt-1">{description}</CardDescription>
        )}
        {trend && (
          <p
            className={cn(
              "text-sm font-medium mt-2 px-2 py-1 rounded-md inline-flex items-center gap-1",
              trend.isPositive
                ? "text-green-700 bg-green-100 dark:text-green-300 dark:bg-green-900/30"
                : "text-red-700 bg-red-100 dark:text-red-300 dark:bg-red-900/30"
            )}
          >
            {trend.isPositive ? "↗" : "↘"} {trend.isPercentage ? `${trend.value}%` : trend.value} this week
          </p>
        )}
      </CardContent>
    </Card>
  )
}

