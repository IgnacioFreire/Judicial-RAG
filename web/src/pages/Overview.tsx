import { useEffect, useState } from "react"
import { Link } from "react-router"

import { PageHeader } from "@/components/PageHeader"
import { RunBar } from "@/components/RunBar"
import { Alert } from "@/components/ui/alert"
import { Card } from "@/components/ui/card"
import { useI18n } from "@/i18n/context"
import { loadDocuments } from "@/lib/api"
import type { DocumentRow } from "@/lib/types"
import { useWorkspace } from "@/workspace"

function Metric({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <Card className="min-w-0">
      <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">{label}</p>
      <p className="mt-2 text-3xl font-semibold tracking-tight">{value}</p>
      <p className="mt-1 text-sm text-muted-foreground">{hint}</p>
    </Card>
  )
}

export function OverviewPage() {
  const { messages } = useI18n()
  const t = messages.overview
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
    <div className="space-y-6">
      <PageHeader
        title={`⚖️ ${messages.app.name}`}
        description={messages.app.tagline}
        helpKey="overview"
      />
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Metric
          label={t.documents}
          value={String(session.accepted_files.length)}
          hint={t.documentsHint}
        />
        <Metric
          label={t.schema}
          value={session.schema_saved ? t.saved : t.draft}
          hint={
            session.schema_saved
              ? `${session.question_count} ${t.schemaSavedHint}`
              : t.schemaDraftHint
          }
        />
        <Metric
          label={t.questions}
          value={String(session.question_count)}
          hint={t.questionsHint}
        />
        <Metric
          label={t.answered}
          value={session.results ? `${answered}/${totalAnswers}` : messages.common.dash}
          hint={t.answeredHint}
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
        <Alert className="border-destructive/30 bg-destructive/10 text-destructive">
          {session.pipeline_error}
        </Alert>
      ) : null}
      {session.success_message ? (
        <Alert className="border-emerald-500/30 bg-emerald-500/10 text-emerald-800 dark:text-emerald-200">
          {session.success_message}
        </Alert>
      ) : null}
      {session.run_errors.map((message) => (
        <Alert
          key={message}
          className="border-amber-500/30 bg-amber-500/10 text-amber-950 dark:text-amber-100"
        >
          {message}
        </Alert>
      ))}
      <Card>
        <h2 className="font-semibold tracking-tight">{t.recent}</h2>
        {rows.length === 0 ? (
          <p className="mt-2 text-sm text-muted-foreground">{t.noDocuments}</p>
        ) : (
          <ul className="mt-3 space-y-2 text-sm">
            {rows.slice(-5).reverse().map((row) => (
              <li key={row.name} className="flex items-center justify-between gap-3">
                <Link
                  className="font-medium text-foreground underline"
                  to={`/documents/${encodeURIComponent(row.name)}`}
                >
                  {row.name}
                </Link>
                <span className="text-muted-foreground">{row.status}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  )
}
