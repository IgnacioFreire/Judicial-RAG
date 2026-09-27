import * as React from "react"

import { cn } from "@/lib/utils"

export function Input({ className, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      className={cn(
        "flex h-10 w-full rounded-xl border border-input bg-background px-3 py-1 text-sm outline-none disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    />
  )
}
