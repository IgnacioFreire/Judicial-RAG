import { useState } from "react"
import { ListChecks } from "lucide-react"

import { HelpButton } from "@/components/HelpButton"
import { QuestionEditor } from "@/components/QuestionEditor"
import { Alert } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { saveSchema } from "@/lib/api"
import type { QuestionDraft } from "@/lib/types"

type Props = {
  disabled: boolean
  onSaved: (count: number) => void
}

function emptyDraft(): QuestionDraft {
  return {
    id: crypto.randomUUID(),
    label: "",
    question: "",
    question_type: "extraction",
    output_format: "",
    notes: "",
    categories: [],
    expanded: true,
  }
}

export function QuestionForm({ disabled, onSaved }: Props) {
  const [drafts, setDrafts] = useState<QuestionDraft[]>([emptyDraft()])
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function handleSave() {
    const result = await saveSchema(drafts)
    if (!result.saved) {
      const prefix =
        result.error?.question_index != null
          ? `Question ${result.error.question_index + 1}: `
          : ""
      setError(`${prefix}${result.error?.message ?? "Schema error"}`)
      setMessage(null)
      return
    }
    setError(null)
    setMessage(`Schema saved — ${result.question_count} question(s).`)
    onSaved(result.question_count)
  }

  return (
    <section className="space-y-3 rounded-2xl border border-border bg-card p-4">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-foreground">
          <ListChecks className="size-4 text-muted-foreground" />
          <h2 className="text-sm font-semibold">Define questions</h2>
        </div>
        <HelpButton helpKey="schema" />
      </div>
      {drafts.map((draft, index) => (
        <QuestionEditor
          key={draft.id}
          draft={draft}
          index={index}
          disabled={disabled}
          onChange={(next) =>
            setDrafts((current) =>
              current.map((row) => (row.id === next.id ? next : row)),
            )
          }
          onRemove={() =>
            setDrafts((current) => current.filter((row) => row.id !== draft.id))
          }
        />
      ))}
      <div className="grid grid-cols-[1fr_3fr] gap-2">
        <Button
          type="button"
          variant="sidebar"
          disabled={disabled}
          onClick={() => setDrafts((current) => [...current, emptyDraft()])}
        >
          Add question
        </Button>
        <Button
          type="button"
          variant="sidebarPrimary"
          disabled={disabled}
          onClick={() => void handleSave()}
        >
          Save schema
        </Button>
      </div>
      {error ? (
        <Alert className="border-red-900/60 bg-red-950/40 text-red-200">{error}</Alert>
      ) : null}
      {message ? (
        <Alert className="border-emerald-900/50 bg-emerald-950/30 text-emerald-200">
          {message}
        </Alert>
      ) : null}
    </section>
  )
}
