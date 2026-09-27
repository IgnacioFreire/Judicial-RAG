import { Play, RotateCcw } from "lucide-react"

import { HelpButton } from "@/components/HelpButton"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { useI18n } from "@/i18n/context"

type Props = {
  canRun: boolean
  processing: boolean
  progress: number | null
  status: string
  onRun: () => void
  onReset: () => void
}

export function RunBar({ canRun, processing, progress, status, onRun, onReset }: Props) {
  const { messages } = useI18n()
  const t = messages.run
  const hint = canRun ? undefined : t.hint
  return (
    <div className="space-y-4 rounded-2xl border border-border bg-card p-5 shadow-sm">
      <div className="flex items-center justify-between gap-2">
        <p className="text-sm font-medium text-foreground">{t.run}</p>
        <HelpButton helpKey="run" />
      </div>
      <div className="grid grid-cols-[2fr_1fr] gap-3">
        <Button type="button" disabled={!canRun} title={hint} onClick={onRun}>
          <Play className="size-4" />
          {t.run}
        </Button>
        <Button type="button" variant="outline" disabled={processing} onClick={onReset}>
          <RotateCcw className="size-4" />
          {t.reset}
        </Button>
      </div>
      {progress != null ? <Progress value={progress} /> : null}
      {status ? <p className="text-sm text-muted-foreground">{status}</p> : null}
    </div>
  )
}
