import type { ReactNode } from "react"

import { cn } from "@/lib/utils"

export function Card({
  className,
  children,
}: {
  className?: string
  children: ReactNode
}) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-zinc-200/80 bg-card p-5 text-card-foreground shadow-sm",
        className,
      )}
    >
      {children}
    </div>
  )
}
