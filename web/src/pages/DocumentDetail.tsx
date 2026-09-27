import { useEffect, useState } from "react"
import { Link, useParams } from "react-router"

import { ResultsViewer } from "@/components/ResultsViewer"
import { Card } from "@/components/ui/card"
import { loadDocument } from "@/lib/api"
import type { DocumentDetail } from "@/lib/types"

function when(value: string | null) {
  if (!value) {
    return "—"
  }
  return new Date(value).toLocaleString()
}

export function DocumentDetailPage() {
  const params = useParams()
  const name = params.name ?? ""
  const [detail, setDetail] = useState<DocumentDetail | null>(null)
  const [missing, setMissing] = useState(false)

  useEffect(() => {
    if (!name) {
      return
    }
    loadDocument(name)
      .then((value) => {
        setDetail(value)
        setMissing(false)
      })
      .catch(() => {
        setDetail(null)
        setMissing(true)
      })
  }, [name])

  if (missing) {
    return (
      <Card>
        <p className="font-medium">Document not found.</p>
        <Link className="mt-2 inline-block text-sm underline" to="/documents">
          Back to documents
        </Link>
      </Card>
    )
  }
  if (!detail) {
    return <p className="text-sm text-zinc-500">Loading…</p>
  }

  return (
    <div className="space-y-5">
      <div>
        <Link className="text-sm text-zinc-500 underline" to="/documents">
          Documents
        </Link>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight">{detail.name}</h1>
        <p className="mt-1 text-sm text-zinc-500">
          {detail.status} · accepted {when(detail.accepted_at)} · finished{" "}
          {when(detail.finished_at)}
        </p>
      </div>
      {detail.answers ? (
        <ResultsViewer results={[detail.answers]} />
      ) : (
        <Card>
          <p className="text-sm text-zinc-500">
            No answers for this PDF yet. A ready or failed file has no answer list.
          </p>
        </Card>
      )}
    </div>
  )
}
