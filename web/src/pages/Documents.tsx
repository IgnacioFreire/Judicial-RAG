import { useEffect, useState } from "react"
import { Link } from "react-router"

import { Uploader } from "@/components/Uploader"
import { Card } from "@/components/ui/card"
import { loadDocuments } from "@/lib/api"
import type { DocumentRow } from "@/lib/types"
import { useWorkspace } from "@/workspace"

function when(value: string | null) {
  if (!value) {
    return "—"
  }
  return new Date(value).toLocaleString()
}

export function DocumentsPage() {
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
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Documents</h1>
        <p className="mt-1 text-sm text-zinc-500">
          Accepted PDFs in this session, with status and times.
        </p>
      </div>
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
      <div className="overflow-hidden rounded-2xl border border-zinc-200 bg-white">
        <table className="w-full text-left text-sm">
          <thead className="bg-zinc-50 text-xs tracking-wide text-zinc-500 uppercase">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Accepted</th>
              <th className="px-4 py-3">Finished</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td className="px-4 py-6 text-zinc-500" colSpan={4}>
                  No PDFs in this session yet.
                </td>
              </tr>
            ) : (
              rows.map((row) => (
                <tr key={row.name} className="border-t border-zinc-100">
                  <td className="px-4 py-3">
                    <Link
                      className="font-medium underline"
                      to={`/documents/${encodeURIComponent(row.name)}`}
                    >
                      {row.name}
                    </Link>
                  </td>
                  <td className="px-4 py-3">{row.status}</td>
                  <td className="px-4 py-3">{when(row.accepted_at)}</td>
                  <td className="px-4 py-3">{when(row.finished_at)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
