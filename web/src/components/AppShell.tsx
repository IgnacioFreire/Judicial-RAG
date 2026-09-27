import { FileText, LayoutDashboard, Settings } from "lucide-react"
import { NavLink, Outlet } from "react-router"

import { ProfileMenu } from "@/components/ProfileMenu"
import { useI18n } from "@/i18n/context"
import { cn } from "@/lib/utils"

export function AppShell() {
  const { messages } = useI18n()

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    cn(
      "flex items-center gap-2 rounded-xl px-3 py-2 text-sm transition-colors",
      isActive
        ? "bg-sidebar-accent text-sidebar-foreground font-medium"
        : "text-sidebar-muted hover:bg-sidebar-accent/80 hover:text-sidebar-foreground",
    )

  return (
    <div className="min-h-screen bg-background p-3 md:p-4">
      <div
        className="mx-auto flex min-h-[calc(100vh-1.5rem)] max-w-[1600px] overflow-hidden rounded-3xl border border-border bg-card shadow-sm"
      >
        <aside className="flex w-64 shrink-0 flex-col bg-sidebar text-sidebar-foreground">
          <div className="px-5 py-6">
            <p className="text-sm font-semibold tracking-tight">⚖️ {messages.app.name}</p>
            <p className="text-xs text-sidebar-muted">{messages.app.workspace}</p>
          </div>
          <nav className="space-y-1 px-3">
            <NavLink to="/" end className={linkClass}>
              <LayoutDashboard className="size-4" />
              {messages.nav.overview}
            </NavLink>
            <NavLink to="/documents" className={linkClass}>
              <FileText className="size-4" />
              {messages.nav.documents}
            </NavLink>
            <NavLink to="/settings" className={linkClass}>
              <Settings className="size-4" />
              {messages.nav.settings}
            </NavLink>
          </nav>
        </aside>
        <div className="min-w-0 flex-1 bg-canvas">
          <header className="flex items-center justify-end border-b border-border px-6 py-4">
            <ProfileMenu />
          </header>
          <div className="p-6">
            <Outlet />
          </div>
        </div>
      </div>
    </div>
  )
}
