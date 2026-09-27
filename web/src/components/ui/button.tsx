import { cva, type VariantProps } from "class-variance-authority"
import * as React from "react"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-xl text-sm font-medium whitespace-nowrap transition-colors disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-zinc-950 text-zinc-50 hover:bg-zinc-800",
        outline: "border border-zinc-200 bg-white hover:bg-zinc-50",
        ghost: "hover:bg-zinc-100",
        sidebar:
          "border border-zinc-800 bg-zinc-900 text-zinc-100 hover:bg-zinc-800",
        sidebarPrimary: "bg-white text-zinc-950 hover:bg-zinc-200",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-8 px-3",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
)

export function Button({
  className,
  variant,
  size,
  ...props
}: React.ComponentProps<"button"> & VariantProps<typeof buttonVariants>) {
  return (
    <button className={cn(buttonVariants({ variant, size, className }))} {...props} />
  )
}
