import { useEffect, useState } from "react"
import { Link } from "react-router"

import { PageHeader } from "@/components/PageHeader"
import { StatusBadge } from "@/components/StatusBadge"
import { Uploader } from "@/components/Uploader"
import { useI18n } from "@/i18n/context"
import { loadDocuments } from "@/lib/api"
import type { DocumentRow } from "@/lib/types"
import { useWorkspace } from "@/workspace"

function when(value: string | null, dash: string) {
  if (!value) {
    return dash
  }
  return new Date(value).toLocaleString()
}

export function DocumentsPage() {
  const { messages } = useI18n()
  const t = messages.documents
  const { session, setSession, rejected, setRejected, fileRef } = useWorkspace()
  const [rows, setRows] = useState<DocumentRow[]>([])

  function refresh() {
    loadDocuments()
      .then(setRows)
      .catch(() => setRows([]))
  }

  useEffect(() => {
    refresh()
  }, [session.accepted_files.join("|"), session.is_processing])

  return (
    <div className="space-y-6">
      <PageHeader title={t.title} description={t.subtitle} helpKey="documents" />
      <section className="rounded-2xl border border-border bg-card p-5 shadow-sm">
        <Uploader
          files={session.accepted_files}
          rejected={rejected}
          emptyHint
          disabled={session.is_processing}
          maxMb={session.max_upload_mb}
          fileRef={fileRef}
          onChange={(accepted, nextRejected) => {
            setRejected(nextRejected)
            setSession((current) =>
              current ? { ...current, accepted_files: accepted } : current,
            )
            refresh()
          }}
        />
      </section>
      <section className="overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <h2 className="text-base font-semibold tracking-tight">{t.title}</h2>
          <p className="text-sm text-muted-foreground">
            {rows.length} {t.count}
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs text-muted-foreground">
              <tr className="border-b border-border">
                <th className="px-5 py-3 font-medium">{t.name}</th>
                <th className="px-5 py-3 font-medium">{t.status}</th>
                <th className="px-5 py-3 font-medium">{t.accepted}</th>
                <th className="px-5 py-3 font-medium">{t.finished}</th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 ? (
                <tr>
                  <td className="px-5 py-10 text-muted-foreground" colSpan={4}>
                    {t.empty}
                  </td>
                </tr>
              ) : (
                rows.map((row) => (
                  <tr key={row.name} className="border-b border-border last:border-b-0 hover:bg-muted/40">
                    <td className="px-5 py-3.5">
                      <Link
                        className="font-medium text-foreground hover:underline"
                        to={`/documents/${encodeURIComponent(row.name)}`}
                      >
                        {row.name}
                      </Link>
                    </td>
                    <td className="px-5 py-3.5">
                      <StatusBadge status={row.status} />
                    </td>
                    <td className="px-5 py-3.5 text-muted-foreground">
                      {when(row.accepted_at, messages.common.dash)}
                    </td>
                    <td className="px-5 py-3.5 text-muted-foreground">
                      {when(row.finished_at, messages.common.dash)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
