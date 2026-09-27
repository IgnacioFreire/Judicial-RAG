import type { ReactNode } from "react"

import { HelpButton } from "@/components/HelpButton"
import type { Messages } from "@/i18n/en"

type HelpKey = keyof Messages["help"]

type Props = {
  title: string
  description?: string
  helpKey?: HelpKey
  children?: ReactNode
}

export function PageHeader({ title, description, helpKey, children }: Props) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">{title}</h1>
          {helpKey ? <HelpButton helpKey={helpKey} /> : null}
        </div>
        {description ? (
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">{description}</p>
        ) : null}
      </div>
      {children}
    </div>
  )
}
