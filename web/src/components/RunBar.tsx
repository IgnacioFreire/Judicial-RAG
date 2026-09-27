import { Play, RotateCcw } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"

type Props = {
  canRun: boolean
  processing: boolean
  progress: number | null
  status: string
  onRun: () => void
  onReset: () => void
}

export function RunBar({ canRun, processing, progress, status, onRun, onReset }: Props) {
  const hint = canRun ? undefined : "Upload PDFs and save a schema first."
  return (
    <div className="space-y-4 rounded-2xl border border-zinc-200/80 bg-white p-5 shadow-sm">
      <div className="grid grid-cols-[2fr_1fr] gap-3">
        <Button type="button" disabled={!canRun} title={hint} onClick={onRun}>
          <Play className="size-4" />
          Run pipeline
        </Button>
        <Button type="button" variant="outline" disabled={processing} onClick={onReset}>
          <RotateCcw className="size-4" />
          Reset
        </Button>
      </div>
      {progress != null ? <Progress value={progress} /> : null}
      {status ? <p className="text-sm text-muted-foreground">{status}</p> : null}
    </div>
  )
}
