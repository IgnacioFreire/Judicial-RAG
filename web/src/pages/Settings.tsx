import { AdvancedSettings } from "@/components/AdvancedSettings"
import { PageHeader } from "@/components/PageHeader"
import { QuestionForm } from "@/components/QuestionForm"
import { Card } from "@/components/ui/card"
import { useI18n } from "@/i18n/context"
import { TYPE_OPTIONS } from "@/lib/types"
import { useWorkspace } from "@/workspace"

export function SettingsPage() {
  const { messages } = useI18n()
  const t = messages.settings
  const { session, setSession } = useWorkspace()
  return (
    <div className="space-y-6">
      <PageHeader title={t.title} description={t.subtitle} helpKey="settings" />
      <div className="space-y-4 rounded-2xl border border-border bg-card p-5 shadow-sm">
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
        <AdvancedSettings
          session={session}
          disabled={session.is_processing}
          onChange={(next) => setSession(next)}
        />
      </div>
      <Card>
        <h2 className="font-semibold">{t.typesTitle}</h2>
        <p className="mt-1 text-sm text-muted-foreground">{t.typesIntro}</p>
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
