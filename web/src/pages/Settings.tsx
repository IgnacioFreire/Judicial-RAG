import { AdvancedSettings } from "@/components/AdvancedSettings"
import { QuestionForm } from "@/components/QuestionForm"
import { Card } from "@/components/ui/card"
import { TYPE_OPTIONS } from "@/lib/types"
import { useWorkspace } from "@/workspace"

export function SettingsPage() {
  const { session, setSession } = useWorkspace()
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="mt-1 text-sm text-zinc-500">
          Questions, save schema, and the three session tiers.
        </p>
      </div>
      <div className="rounded-3xl bg-zinc-950 p-4 text-zinc-100">
        <QuestionForm
          disabled={session.is_processing}
          onSaved={(count) =>
            setSession((current) =>
              current
                ? { ...current, schema_saved: true, question_count: count }
                : current,
            )
          }
        />
        <div className="mt-4">
          <AdvancedSettings
            session={session}
            disabled={session.is_processing}
            onChange={(next) => setSession(next)}
          />
        </div>
      </div>
      <Card>
        <h2 className="font-semibold">Question types</h2>
        <p className="mt-1 text-sm text-zinc-500">
          Each type uses the instruction in pipeline/rag_agent.py. The editable text is
          the question, the output format, and the notes.
        </p>
        <ul className="mt-3 space-y-2 text-sm">
          {TYPE_OPTIONS.map((option) => (
            <li key={option.value}>
              <span className="font-medium">{option.value}</span> — {option.label}
            </li>
          ))}
        </ul>
      </Card>
    </div>
  )
}
