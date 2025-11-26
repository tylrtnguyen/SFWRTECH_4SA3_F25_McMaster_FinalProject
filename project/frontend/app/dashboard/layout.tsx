import { redirect } from "next/navigation"
import { createClient } from "@/lib/supabase/server"
import { DashboardLayout } from "@/components/dashboard-layout"

export default async function Layout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient()
  
  // Refresh session first to ensure we have the latest auth state
  // await supabase.auth.getSession()
  
  // const {
  //   data: { user },
  // } = await supabase.auth.getUser()

  // if (!user) {
  //   redirect("/401")
  // }

  return <DashboardLayout>{children}</DashboardLayout>
}

