import { cn } from "@/lib/utils"

const tones: Record<string, string> = {
  ready: "bg-muted text-muted-foreground",
  queued: "bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-200",
  extracting: "bg-sky-100 text-sky-900 dark:bg-sky-950 dark:text-sky-200",
  embedding: "bg-sky-100 text-sky-900 dark:bg-sky-950 dark:text-sky-200",
  answering: "bg-sky-100 text-sky-900 dark:bg-sky-950 dark:text-sky-200",
  done: "bg-emerald-100 text-emerald-900 dark:bg-emerald-950 dark:text-emerald-200",
  failed: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-200",
}

export function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2 py-0.5 text-xs font-medium capitalize",
        tones[status] ?? tones.ready,
      )}
    >
      {status}
    </span>
  )
}
