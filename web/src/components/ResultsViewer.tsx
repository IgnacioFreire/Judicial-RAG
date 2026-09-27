import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import type { AgentAnswer, DocumentAnswers } from "@/lib/types"

const CONFIDENCE_CLASS: Record<AgentAnswer["confidence"], string> = {
  high: "bg-emerald-100 text-emerald-800",
  medium: "bg-orange-100 text-orange-800",
  low: "bg-red-100 text-red-800",
  not_found: "bg-zinc-100 text-zinc-600",
}

function AnswerCard({ answer }: { answer: AgentAnswer }) {
  const source =
    answer.answer_source === "direct"
      ? "Extracted directly"
      : answer.answer_source === "inferred"
        ? "Inferred through reasoning"
        : null
  return (
    <div className="space-y-2">
      <div className="flex items-start justify-between gap-2">
        <p className="font-semibold tracking-tight">{answer.question.label}</p>
        <span title="Confidence assigned by the agent.">
          <Badge className={CONFIDENCE_CLASS[answer.confidence]}>
            {answer.confidence}
          </Badge>
        </span>
      </div>
      {answer.answer ? (
        <p>{answer.answer}</p>
      ) : (
        <p className="text-sm text-muted-foreground">No answer found.</p>
      )}
      {source ? <p className="text-sm text-muted-foreground">Source: {source}</p> : null}
      {answer.citation ? (
        <Card className="bg-zinc-50 p-4 shadow-none">
          <p className="text-xs text-muted-foreground">
            Page {answer.citation.page} — score {answer.citation.score.toFixed(2)}
          </p>
          <pre className="mt-1 whitespace-pre-wrap font-sans text-sm">
            {answer.citation.text}
          </pre>
        </Card>
      ) : null}
    </div>
  )
}

export function ResultsViewer({ results }: { results: DocumentAnswers[] }) {
  if (results.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No results yet. Run the pipeline first.</p>
    )
  }
  return (
    <section className="space-y-3">
      <h2 className="text-lg font-semibold tracking-tight">Results</h2>
      {results.map((doc) => {
        const answered = doc.answers.filter((row) => row.confidence !== "not_found").length
        const ratio = doc.answers.length === 0 ? 0 : (answered / doc.answers.length) * 100
        return (
          <details
            key={doc.document}
            open
            className="rounded-2xl border border-zinc-200/80 bg-white p-5 shadow-sm"
          >
            <summary className="cursor-pointer font-medium tracking-tight">
              {doc.document} — {answered}/{doc.answers.length} answered
            </summary>
            <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-zinc-100">
              <div
                className="h-full rounded-full bg-zinc-950"
                style={{ width: `${ratio}%` }}
              />
            </div>
            <div className="mt-4 space-y-3">
              {doc.answers.map((answer, index) => (
                <div key={`${doc.document}-${index}`}>
                  <AnswerCard answer={answer} />
                  {index < doc.answers.length - 1 ? <Separator className="my-3" /> : null}
                </div>
              ))}
            </div>
          </details>
        )
      })}
    </section>
  )
}
