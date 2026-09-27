import { useEffect, useState } from "react"
import { Link } from "react-router"

import { PageHeader } from "@/components/PageHeader"
import { Uploader } from "@/components/Uploader"
import { Card } from "@/components/ui/card"
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
      <Card>
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
      </Card>
      <div className="overflow-hidden rounded-2xl border border-border bg-card">
        <table className="w-full text-left text-sm">
          <thead className="bg-muted text-xs tracking-wide text-muted-foreground uppercase">
            <tr>
              <th className="px-4 py-3">{t.name}</th>
              <th className="px-4 py-3">{t.status}</th>
              <th className="px-4 py-3">{t.accepted}</th>
              <th className="px-4 py-3">{t.finished}</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td className="px-4 py-6 text-muted-foreground" colSpan={4}>
                  {t.empty}
                </td>
              </tr>
            ) : (
              rows.map((row) => (
                <tr key={row.name} className="border-t border-border">
                  <td className="px-4 py-3">
                    <Link
                      className="font-medium text-foreground underline"
                      to={`/documents/${encodeURIComponent(row.name)}`}
                    >
                      {row.name}
                    </Link>
                  </td>
                  <td className="px-4 py-3">{row.status}</td>
                  <td className="px-4 py-3">{when(row.accepted_at, messages.common.dash)}</td>
                  <td className="px-4 py-3">{when(row.finished_at, messages.common.dash)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
