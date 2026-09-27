import {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
  type RefObject,
} from "react"

import { loadSession, resetSession, runPipeline } from "@/lib/api"
import type { SessionView } from "@/lib/types"

type Workspace = {
  session: SessionView
  setSession: (value: SessionView | ((current: SessionView | null) => SessionView | null)) => void
  reload: () => Promise<void>
  rejected: string[]
  setRejected: (value: string[]) => void
  fileRef: RefObject<HTMLInputElement | null>
  status: string
  progress: number | null
  canRun: boolean
  run: () => Promise<void>
  reset: () => Promise<void>
}

const WorkspaceContext = createContext<Workspace | null>(null)

export function useWorkspace(): Workspace {
  const value = useContext(WorkspaceContext)
  if (!value) {
    throw new Error("Workspace is missing")
  }
  return value
}

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [session, setSessionState] = useState<SessionView | null>(null)
  const [rejected, setRejected] = useState<string[]>([])
  const [status, setStatus] = useState("")
  const [progress, setProgress] = useState<number | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  async function reload() {
    setSessionState(await loadSession())
  }

  useEffect(() => {
    reload().catch((error: Error) => setLoadError(error.message))
  }, [])

  if (loadError) {
    return <p className="p-6 text-red-700">{loadError}</p>
  }
  if (!session) {
    return <p className="p-6 text-zinc-500">Loading…</p>
  }

  const processing = session.is_processing
  const canRun =
    session.accepted_files.length > 0 && session.schema_saved && !processing

  function setSession(
    value: SessionView | ((current: SessionView | null) => SessionView | null),
  ) {
    setSessionState((current) => {
      const next = typeof value === "function" ? value(current) : value
      return next
    })
  }

  async function reset() {
    const next = await resetSession()
    setSessionState(next)
    setRejected([])
    setStatus("")
    setProgress(null)
    if (fileRef.current) {
      fileRef.current.value = ""
    }
  }

  async function run() {
    setSessionState((current) =>
      current
        ? {
            ...current,
            is_processing: true,
            results: null,
            run_errors: [],
            pipeline_error: null,
            success_message: null,
          }
        : current,
    )
    setStatus("Starting...")
    setProgress(0)
    try {
      await runPipeline((event) => {
        if (event.total > 0) {
          setProgress((event.current / event.total) * 100)
          setStatus(event.message)
        } else {
          setStatus(event.message)
        }
        if (event.type === "done" || event.type === "failed") {
          if (event.type === "done") {
            setProgress(100)
            setStatus("Complete.")
          }
          void reload()
        }
      })
    } catch (error) {
      setSessionState((current) =>
        current
          ? {
              ...current,
              is_processing: false,
              pipeline_error: error instanceof Error ? error.message : String(error),
            }
          : current,
      )
    }
  }

  return (
    <WorkspaceContext.Provider
      value={{
        session,
        setSession,
        reload,
        rejected,
        setRejected,
        fileRef,
        status,
        progress,
        canRun,
        run,
        reset,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  )
}
