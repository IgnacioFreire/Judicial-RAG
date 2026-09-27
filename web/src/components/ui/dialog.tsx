import { useEffect, useRef, type ReactNode } from "react"

import { cn } from "@/lib/utils"

type Props = {
  open: boolean
  onClose: () => void
  title: string
  children: ReactNode
  className?: string
}

export function Dialog({ open, onClose, title, children, className }: Props) {
  const ref = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    const node = ref.current
    if (!node) {
      return
    }
    if (open && !node.open) {
      node.showModal()
    }
    if (!open && node.open) {
      node.close()
    }
  }, [open])

  return (
    <dialog
      ref={ref}
      className={cn(
        "fixed top-1/2 left-1/2 z-50 w-[min(100%,28rem)] -translate-x-1/2 -translate-y-1/2 rounded-2xl border border-border bg-card p-0 text-card-foreground shadow-xl backdrop:bg-black/40",
        className,
      )}
      onCancel={(event) => {
        event.preventDefault()
        onClose()
      }}
      onClick={(event) => {
        if (event.target === ref.current) {
          onClose()
        }
      }}
    >
      <div className="border-b border-border px-5 py-4">
        <h2 className="text-base font-semibold tracking-tight">{title}</h2>
      </div>
      <div className="px-5 py-4 text-sm leading-relaxed text-muted-foreground">{children}</div>
    </dialog>
  )
}
