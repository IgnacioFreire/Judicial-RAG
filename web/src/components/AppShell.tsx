import { FileText, LayoutDashboard, Scale, Settings } from "lucide-react"
import { NavLink, Outlet } from "react-router"

import { ProfileMenu } from "@/components/ProfileMenu"
import { useI18n } from "@/i18n/context"
import { cn } from "@/lib/utils"

export function AppShell() {
  const { messages } = useI18n()

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    cn(
      "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors",
      isActive
        ? "bg-sidebar-accent font-medium text-sidebar-foreground"
        : "text-sidebar-muted hover:bg-sidebar-accent/70 hover:text-sidebar-foreground",
    )

  return (
    <div className="flex min-h-screen bg-canvas">
      <aside className="flex w-64 shrink-0 flex-col border-r border-border bg-sidebar text-sidebar-foreground">
        <div className="flex items-center gap-2 px-5 py-5">
          <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Scale className="size-4" />
          </span>
          <div>
            <p className="text-sm font-semibold tracking-tight">{messages.app.name}</p>
            <p className="text-xs text-sidebar-muted">{messages.app.workspace}</p>
          </div>
        </div>
        <nav className="flex-1 space-y-0.5 px-3">
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
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 items-center justify-end border-b border-border bg-card px-6">
          <ProfileMenu />
        </header>
        <main className="flex-1 px-6 py-8 md:px-8">
          <div className="mx-auto max-w-6xl">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
