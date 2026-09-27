import { useEffect, useState } from "react"
import { Link, useParams } from "react-router"

import { PageHeader } from "@/components/PageHeader"
import { ResultsViewer } from "@/components/ResultsViewer"
import { Card } from "@/components/ui/card"
import { useI18n } from "@/i18n/context"
import { loadDocument } from "@/lib/api"
import type { DocumentDetail } from "@/lib/types"

function when(value: string | null, dash: string) {
  if (!value) {
    return dash
  }
  return new Date(value).toLocaleString()
}

export function DocumentDetailPage() {
  const { messages } = useI18n()
  const t = messages.documentDetail
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
        <p className="font-medium">{t.notFound}</p>
        <Link className="mt-2 inline-block text-sm underline" to="/documents">
          {t.backLink}
        </Link>
      </Card>
    )
  }
  if (!detail) {
    return <p className="text-sm text-muted-foreground">{messages.common.loading}</p>
  }

  return (
    <div className="space-y-6">
      <div>
        <Link className="text-sm text-muted-foreground underline" to="/documents">
          {t.back}
        </Link>
        <PageHeader
          title={detail.name}
          helpKey="documentDetail"
          description={`${detail.status} · ${t.accepted} ${when(detail.accepted_at, messages.common.dash)} · ${t.finished} ${when(detail.finished_at, messages.common.dash)}`}
        />
      </div>
      {detail.answers ? (
        <ResultsViewer results={[detail.answers]} />
      ) : (
        <Card>
          <p className="text-sm text-muted-foreground">{t.noAnswers}</p>
        </Card>
      )}
    </div>
  )
}
