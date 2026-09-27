import type { ReactNode } from "react"

import { cn } from "@/lib/utils"

export function Alert({
  className,
  children,
}: {
  className?: string
  children: ReactNode
}) {
  return (
    <div
      className={cn("rounded-xl border px-3 py-2 text-sm", className)}
      role="status"
    >
      {children}
    </div>
  )
}
