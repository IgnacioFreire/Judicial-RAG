import { useEffect, useRef, useState } from "react"
import { FileText, Loader2, Scale } from "lucide-react"

import { AdvancedSettings } from "@/components/AdvancedSettings"
import { QuestionForm } from "@/components/QuestionForm"
import { ResultsViewer } from "@/components/ResultsViewer"
import { RunBar } from "@/components/RunBar"
import { Uploader } from "@/components/Uploader"
import { Alert } from "@/components/ui/alert"
import { Card } from "@/components/ui/card"
import { loadSession, resetSession, runPipeline } from "@/lib/api"
import type { SessionView } from "@/lib/types"

function Metric({
  label,
  value,
  hint,
}: {
  label: string
  value: string
  hint: string
}) {
  return (
    <Card className="min-w-0">
      <p className="text-xs font-medium tracking-wide text-zinc-500 uppercase">{label}</p>
      <p className="mt-2 text-3xl font-semibold tracking-tight">{value}</p>
      <p className="mt-1 text-sm text-muted-foreground">{hint}</p>
    </Card>
  )
}

export default function App() {
  const [session, setSession] = useState<SessionView | null>(null)
  const [rejected, setRejected] = useState<string[]>([])
  const [status, setStatus] = useState("")
  const [progress, setProgress] = useState<number | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    loadSession()
      .then(setSession)
      .catch((error: Error) => setLoadError(error.message))
  }, [])

  if (loadError) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-100 p-6">
        <p className="text-destructive">{loadError}</p>
      </div>
    )
  }
  if (!session) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-100 text-muted-foreground">
        <Loader2 className="mr-2 size-4 animate-spin" />
        Loading…
      </div>
    )
  }

  const processing = session.is_processing
  const canRun =
    session.accepted_files.length > 0 && session.schema_saved && !processing
  const answered =
    session.results?.reduce(
      (sum, doc) =>
        sum + doc.answers.filter((row) => row.confidence !== "not_found").length,
      0,
    ) ?? 0
  const totalAnswers =
    session.results?.reduce((sum, doc) => sum + doc.answers.length, 0) ?? 0

  async function handleReset() {
    const next = await resetSession()
    setSession(next)
    setRejected([])
    setStatus("")
    setProgress(null)
    if (fileRef.current) {
      fileRef.current.value = ""
    }
  }

  async function handleRun() {
    setSession((current) =>
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
        if (event.type === "done") {
          setProgress(100)
          setStatus("Complete.")
          void loadSession().then(setSession)
        }
        if (event.type === "failed") {
          void loadSession().then(setSession)
        }
      })
    } catch (error) {
      setSession((current) =>
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
    <div className="min-h-screen bg-zinc-100 p-3 md:p-4">
      <div className="mx-auto flex min-h-[calc(100vh-1.5rem)] max-w-[1600px] overflow-hidden rounded-3xl bg-white shadow-sm ring-1 ring-zinc-200/70 md:min-h-[calc(100vh-2rem)]">
        <aside className="flex w-[22rem] shrink-0 flex-col bg-zinc-950 text-zinc-100">
          <div className="flex items-center gap-3 px-5 py-6">
            <div className="flex size-10 items-center justify-center rounded-2xl bg-zinc-100 text-zinc-950">
              <Scale className="size-5" />
            </div>
            <div>
              <p className="text-sm font-semibold tracking-tight">⚖️ Judicial RAG</p>
              <p className="text-xs text-zinc-500">Workspace</p>
            </div>
          </div>
          <div className="flex-1 space-y-3 overflow-y-auto px-3 pb-6">
            <Uploader
              files={session.accepted_files}
              rejected={rejected}
              emptyHint
              disabled={processing}
              maxMb={session.max_upload_mb}
              fileRef={fileRef}
              onChange={(accepted, nextRejected) => {
                setRejected(nextRejected)
                setSession((current) =>
                  current ? { ...current, accepted_files: accepted } : current,
                )
              }}
            />
            <QuestionForm
              disabled={processing}
              onSaved={(count) =>
                setSession((current) =>
                  current
                    ? { ...current, schema_saved: true, question_count: count }
                    : current,
                )
              }
            />
            <AdvancedSettings
              session={session}
              disabled={processing}
              onChange={setSession}
            />
          </div>
        </aside>
        <main className="min-w-0 flex-1 bg-zinc-50/90">
          <header className="flex flex-wrap items-end justify-between gap-3 border-b border-zinc-200/80 px-6 py-5">
            <div>
              <p className="text-sm text-zinc-500">Overview</p>
              <h1 className="text-2xl font-semibold tracking-tight">
                ⚖️ Judicial RAG
              </h1>
              <p className="mt-1 text-sm text-muted-foreground">
                Extract and classify variables from judicial PDF documents.
              </p>
            </div>
            <div className="flex items-center gap-2 rounded-full bg-white px-3 py-1.5 text-xs font-medium text-zinc-600 ring-1 ring-zinc-200">
              {processing ? (
                <>
                  <Loader2 className="size-3.5 animate-spin" />
                  Running
                </>
              ) : (
                "Session"
              )}
            </div>
          </header>
          <div className="space-y-5 p-6">
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <Metric
                label="Documents"
                value={String(session.accepted_files.length)}
                hint="PDFs in this session"
              />
              <Metric
                label="Schema"
                value={session.schema_saved ? "Saved" : "Draft"}
                hint={
                  session.schema_saved
                    ? `${session.question_count} question(s)`
                    : "Save schema to run"
                }
              />
              <Metric
                label="Questions"
                value={String(session.question_count)}
                hint="On the saved schema"
              />
              <Metric
                label="Answered"
                value={session.results ? `${answered}/${totalAnswers}` : "—"}
                hint="Rows that are not not_found"
              />
            </div>
            <RunBar
              canRun={canRun}
              processing={processing}
              progress={progress}
              status={status}
              onRun={() => void handleRun()}
              onReset={() => void handleReset()}
            />
            {session.pipeline_error ? (
              <Alert className="border-red-200 bg-red-50 text-red-800">
                {session.pipeline_error}
              </Alert>
            ) : null}
            {session.success_message ? (
              <Alert className="border-emerald-200 bg-emerald-50 text-emerald-800">
                {session.success_message}
              </Alert>
            ) : null}
            {session.run_errors.map((message) => (
              <Alert key={message} className="border-amber-200 bg-amber-50 text-amber-900">
                {message}
              </Alert>
            ))}
            {session.results ? (
              <ResultsViewer results={session.results} />
            ) : (
              <Card className="flex items-center gap-4 p-6 text-sm text-muted-foreground">
                <div className="flex size-12 items-center justify-center rounded-2xl bg-zinc-100">
                  <FileText className="size-5" />
                </div>
                <div>
                  <p className="font-medium text-zinc-900">No results yet</p>
                  <p>Run the pipeline after you upload PDFs and save a schema.</p>
                </div>
              </Card>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}
