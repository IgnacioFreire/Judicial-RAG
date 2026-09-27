import { CircleHelp } from "lucide-react"
import { useState } from "react"

import { Dialog } from "@/components/ui/dialog"
import { useI18n } from "@/i18n/context"
import type { Messages } from "@/i18n/en"

type HelpKey = keyof Messages["help"]

type Props = {
  helpKey: HelpKey
  className?: string
}

export function HelpButton({ helpKey, className }: Props) {
  const { help, messages } = useI18n()
  const [open, setOpen] = useState(false)
  const copy = help(helpKey)

  return (
    <>
      <button
        type="button"
        className={
          className ??
          "inline-flex size-8 items-center justify-center rounded-full text-muted-foreground transition hover:bg-accent hover:text-foreground"
        }
        aria-label={copy.title}
        onClick={(event) => {
          event.stopPropagation()
          setOpen(true)
        }}
      >
        <CircleHelp className="size-4" />
      </button>
      <Dialog open={open} onClose={() => setOpen(false)} title={copy.title}>
        <p>{copy.body}</p>
        <div className="mt-4 flex justify-end">
          <button
            type="button"
            className="rounded-lg bg-primary px-3 py-1.5 text-sm text-primary-foreground"
            onClick={() => setOpen(false)}
          >
            {messages.common.close}
          </button>
        </div>
      </Dialog>
    </>
  )
}
