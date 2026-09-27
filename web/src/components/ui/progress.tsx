import { cn } from "@/lib/utils"

export function Progress({ value }: { value: number }) {
  return (
    <div className="h-2.5 w-full overflow-hidden rounded-full bg-zinc-100">
      <div
        className={cn("h-full rounded-full bg-zinc-950 transition-all")}
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  )
}
