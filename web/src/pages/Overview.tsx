import { useEffect, useState } from "react"
import { Link } from "react-router"

import { RunBar } from "@/components/RunBar"
import { Alert } from "@/components/ui/alert"
import { Card } from "@/components/ui/card"
import { loadDocuments } from "@/lib/api"
import type { DocumentRow } from "@/lib/types"
import { useWorkspace } from "@/workspace"

function Metric({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <Card className="min-w-0">
      <p className="text-xs font-medium tracking-wide text-zinc-500 uppercase">{label}</p>
      <p className="mt-2 text-3xl font-semibold tracking-tight">{value}</p>
      <p className="mt-1 text-sm text-zinc-500">{hint}</p>
    </Card>
  )
}

export function OverviewPage() {
  const { session, status, progress, canRun, run, reset } = useWorkspace()
  const [rows, setRows] = useState<DocumentRow[]>([])

  useEffect(() => {
    loadDocuments()
      .then(setRows)
      .catch(() => setRows([]))
  }, [session.is_processing, session.accepted_files.length, session.results])

  const answered =
    session.results?.reduce(
      (sum, doc) =>
        sum + doc.answers.filter((row) => row.confidence !== "not_found").length,
      0,
    ) ?? 0
  const totalAnswers =
    session.results?.reduce((sum, doc) => sum + doc.answers.length, 0) ?? 0

  return (
    <div className="space-y-5">
      <div>
        <p className="text-sm text-zinc-500">Overview</p>
        <h1 className="text-2xl font-semibold tracking-tight">⚖️ Judicial RAG</h1>
        <p className="mt-1 text-sm text-zinc-500">
          Extract and classify variables from judicial PDF documents.
        </p>
      </div>
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
        processing={session.is_processing}
        progress={progress}
        status={status}
        onRun={() => void run()}
        onReset={() => void reset()}
      />
      {session.pipeline_error ? (
        <Alert className="border-red-200 bg-red-50 text-red-800">{session.pipeline_error}</Alert>
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
      <Card>
        <h2 className="font-semibold tracking-tight">Recent documents</h2>
        {rows.length === 0 ? (
          <p className="mt-2 text-sm text-zinc-500">No PDFs in this session yet.</p>
        ) : (
          <ul className="mt-3 space-y-2 text-sm">
            {rows.slice(-5).reverse().map((row) => (
              <li key={row.name} className="flex items-center justify-between gap-3">
                <Link className="font-medium underline" to={`/documents/${encodeURIComponent(row.name)}`}>
                  {row.name}
                </Link>
                <span className="text-zinc-500">{row.status}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  )
}
