import { Sidebar } from "./sidebar"
import { Navbar } from "./navbar"

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Navbar />
        <main className="flex-1 overflow-y-auto bg-bg-primary dark:bg-[#1a1d23] p-6">
          {children}
        </main>
      </div>
    </div>
  )
}

