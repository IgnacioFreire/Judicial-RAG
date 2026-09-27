import { useEffect, useState } from "react"
import { FileText, LayoutDashboard, Settings, UserRound } from "lucide-react"
import { NavLink, Outlet } from "react-router"

import { loadProfile } from "@/lib/api"
import type { ProfileView } from "@/lib/types"
import { useWorkspace } from "@/workspace"

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `flex items-center gap-2 rounded-xl px-3 py-2 text-sm ${
    isActive ? "bg-white text-zinc-950" : "text-zinc-300 hover:bg-zinc-900"
  }`

function flag(configured: boolean) {
  return configured ? "Configured" : "Missing"
}

export function AppShell() {
  const { session } = useWorkspace()
  const [open, setOpen] = useState(false)
  const [profile, setProfile] = useState<ProfileView | null>(null)
  const [profileError, setProfileError] = useState<string | null>(null)

  useEffect(() => {
    if (!open) {
      return
    }
    loadProfile()
      .then((value) => {
        setProfile(value)
        setProfileError(null)
      })
      .catch((error: Error) => setProfileError(error.message))
  }, [open, session.is_processing])

  return (
    <div className="min-h-screen bg-zinc-100 p-3 md:p-4">
      <div className="mx-auto flex min-h-[calc(100vh-1.5rem)] max-w-[1600px] overflow-hidden rounded-3xl bg-white shadow-sm ring-1 ring-zinc-200/70">
        <aside className="flex w-64 shrink-0 flex-col bg-zinc-950 text-zinc-100">
          <div className="px-5 py-6">
            <p className="text-sm font-semibold tracking-tight">⚖️ Judicial RAG</p>
            <p className="text-xs text-zinc-500">Workspace</p>
          </div>
          <nav className="space-y-1 px-3">
            <NavLink to="/" end className={linkClass}>
              <LayoutDashboard className="size-4" />
              Overview
            </NavLink>
            <NavLink to="/documents" className={linkClass}>
              <FileText className="size-4" />
              Documents
            </NavLink>
            <NavLink to="/settings" className={linkClass}>
              <Settings className="size-4" />
              Settings
            </NavLink>
          </nav>
        </aside>
        <div className="min-w-0 flex-1 bg-zinc-50/90">
          <header className="flex items-center justify-end border-b border-zinc-200/80 px-6 py-4">
            <div className="relative">
              <button
                type="button"
                className="inline-flex items-center gap-2 rounded-full bg-white px-3 py-1.5 text-sm ring-1 ring-zinc-200"
                onClick={() => setOpen((value) => !value)}
              >
                <UserRound className="size-4" />
                Profile
              </button>
              {open ? (
                <div className="absolute right-0 z-10 mt-2 w-80 rounded-2xl border border-zinc-200 bg-white p-4 text-sm shadow-lg">
                  {profileError ? <p className="text-red-700">{profileError}</p> : null}
                  {profile ? (
                    <dl className="space-y-2">
                      <div>
                        <dt className="text-xs text-zinc-500">Supabase account</dt>
                        <dd>{profile.email || "Not set"}</dd>
                      </div>
                      <div>
                        <dt className="text-xs text-zinc-500">LLM</dt>
                        <dd>
                          {profile.llm_provider} · {profile.llm_model}
                        </dd>
                      </div>
                      <div>
                        <dt className="text-xs text-zinc-500">Active LLM key</dt>
                        <dd>{flag(profile.llm_key_configured)}</dd>
                      </div>
                      <div>
                        <dt className="text-xs text-zinc-500">Embeddings</dt>
                        <dd>
                          {profile.embedding_provider} · {profile.embedding_model}
                        </dd>
                      </div>
                      <div>
                        <dt className="text-xs text-zinc-500">Hugging Face key</dt>
                        <dd>{flag(profile.huggingface_key_configured)}</dd>
                      </div>
                      <div>
                        <dt className="text-xs text-zinc-500">Generation tokens</dt>
                        <dd>
                          in {profile.input_tokens} · out {profile.output_tokens}
                        </dd>
                        <dd className="text-xs text-zinc-500">
                          This session only. Embedding calls are not included.
                        </dd>
                      </div>
                    </dl>
                  ) : null}
                </div>
              ) : null}
            </div>
          </header>
          <div className="p-6">
            <Outlet />
          </div>
        </div>
      </div>
    </div>
  )
}
