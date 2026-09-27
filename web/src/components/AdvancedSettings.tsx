import { useState } from "react"
import { Settings2 } from "lucide-react"

import { HelpButton } from "@/components/HelpButton"
import { Label } from "@/components/ui/label"
import { saveTiers } from "@/lib/api"
import { fieldClass } from "@/lib/styles"
import type { SessionView } from "@/lib/types"

type Props = {
  session: SessionView
  disabled: boolean
  onChange: (session: SessionView) => void
}

export function AdvancedSettings({ session, disabled, onChange }: Props) {
  const [open, setOpen] = useState(false)

  async function patch(
    field: "parser_tier" | "chunk_tier" | "embedding_tier",
    value: string,
  ) {
    onChange(await saveTiers({ [field]: value }))
  }

  return (
    <div className="rounded-2xl border border-border bg-card p-4">
      <div className="flex items-center justify-between gap-2">
        <p className="flex items-center gap-2 text-sm font-semibold text-foreground">
          <Settings2 className="size-4 text-muted-foreground" />
          Advanced settings
        </p>
        <HelpButton helpKey="tiers" />
      </div>
      <details
        open={open}
        className="mt-3"
        onToggle={(event) => setOpen(event.currentTarget.open)}
      >
        <summary className="cursor-pointer text-sm text-muted-foreground">Show tiers</summary>
      <div className="mt-4 space-y-3">
        <div className="space-y-1">
          <Label className="text-muted-foreground">Parser</Label>
          <select
            className={fieldClass}
            value={session.parser_tier}
            disabled={disabled}
            title="Fast reads the text layer. Medium keeps the section structure. Slow spends longer on each page."
            onChange={(event) => void patch("parser_tier", event.target.value)}
          >
            {session.parser_options.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-1">
          <Label className="text-muted-foreground">Chunking</Label>
          <select
            className={fieldClass}
            value={session.chunk_tier}
            disabled={disabled}
            title="Fast cuts every 512 embedding tokens. Medium keeps sections at that same limit. Slow asks the model for a situation sentence before embedding."
            onChange={(event) => void patch("chunk_tier", event.target.value)}
          >
            {session.chunk_options.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-1">
          <Label className="text-muted-foreground">Retrieval</Label>
          <select
            className={fieldClass}
            value={session.embedding_tier}
            disabled={disabled}
            title="Fast searches by vector only. Medium also matches words. Slow reranks a few dozen candidates."
            onChange={(event) => void patch("embedding_tier", event.target.value)}
          >
            {session.embedding_options.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>
      </details>
    </div>
  )
}
