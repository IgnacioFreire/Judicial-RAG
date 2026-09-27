import { useEffect, useState } from "react"
import { Link } from "react-router"
import { ArrowRight, FileUp, ListChecks } from "lucide-react"

import { PageHeader } from "@/components/PageHeader"
import { RunBar } from "@/components/RunBar"
import { StatusBadge } from "@/components/StatusBadge"
import { Alert } from "@/components/ui/alert"
import { useI18n } from "@/i18n/context"
import { loadDocuments } from "@/lib/api"
import type { DocumentRow } from "@/lib/types"
import { useWorkspace } from "@/workspace"

function Stat({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <div className="min-w-0">
      <dt className="text-sm text-muted-foreground">{label}</dt>
      <dd className="mt-1 text-2xl font-semibold tracking-tight">{value}</dd>
      <dd className="mt-1 text-xs text-muted-foreground">{hint}</dd>
    </div>
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
  const recent = rows.slice(-6).reverse()

  return (
    <div className="space-y-8">
      <PageHeader title={t.title} description={messages.app.tagline} helpKey="overview" />

      <section className="overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
        <div className="border-b border-border px-6 py-5">
          <p className="text-sm text-muted-foreground">{t.documents}</p>
          <p className="mt-1 text-4xl font-semibold tracking-tight">
            {session.accepted_files.length}
          </p>
          <p className="mt-1 text-sm text-muted-foreground">{t.documentsHint}</p>
        </div>
        <dl className="grid gap-6 px-6 py-5 sm:grid-cols-3">
          <Stat
            label={t.schema}
            value={session.schema_saved ? t.saved : t.draft}
            hint={
              session.schema_saved
                ? `${session.question_count} ${t.schemaSavedHint}`
                : t.schemaDraftHint
            }
          />
          <Stat
            label={t.questions}
            value={String(session.question_count)}
            hint={t.questionsHint}
          />
          <Stat
            label={t.answered}
            value={session.results ? `${answered}/${totalAnswers}` : messages.common.dash}
            hint={t.answeredHint}
          />
        </dl>
      </section>

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

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.4fr)_minmax(16rem,0.8fr)]">
        <section className="overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
          <div className="flex items-center justify-between border-b border-border px-5 py-4">
            <h2 className="text-base font-semibold tracking-tight">{t.recent}</h2>
            <Link className="text-sm font-medium text-foreground hover:underline" to="/documents">
              {t.viewAll}
            </Link>
          </div>
          {recent.length === 0 ? (
            <p className="px-5 py-8 text-sm text-muted-foreground">{t.noDocuments}</p>
          ) : (
            <ul>
              {recent.map((row) => (
                <li key={row.name} className="border-t border-border first:border-t-0">
                  <Link
                    className="flex items-center justify-between gap-3 px-5 py-3.5 hover:bg-muted/60"
                    to={`/documents/${encodeURIComponent(row.name)}`}
                  >
                    <span className="truncate text-sm font-medium">{row.name}</span>
                    <StatusBadge status={row.status} />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="rounded-2xl border border-border bg-card p-5 shadow-sm">
          <h2 className="text-base font-semibold tracking-tight">{t.nextTitle}</h2>
          <div className="mt-4 space-y-3">
            <Link
              to="/documents"
              className="flex items-start gap-3 rounded-xl border border-border p-3 hover:bg-muted/60"
            >
              <FileUp className="mt-0.5 size-4 text-muted-foreground" />
              <span className="min-w-0 flex-1">
                <span className="block text-sm font-medium">{t.nextUpload}</span>
                <span className="mt-0.5 block text-xs text-muted-foreground">{t.nextUploadHint}</span>
              </span>
              <ArrowRight className="size-4 text-muted-foreground" />
            </Link>
            <Link
              to="/settings"
              className="flex items-start gap-3 rounded-xl border border-border p-3 hover:bg-muted/60"
            >
              <ListChecks className="mt-0.5 size-4 text-muted-foreground" />
              <span className="min-w-0 flex-1">
                <span className="block text-sm font-medium">{t.nextSchema}</span>
                <span className="mt-0.5 block text-xs text-muted-foreground">{t.nextSchemaHint}</span>
              </span>
              <ArrowRight className="size-4 text-muted-foreground" />
            </Link>
          </div>
        </section>
      </div>
    </div>
  )
}
