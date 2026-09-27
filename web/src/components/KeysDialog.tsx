import { useEffect, useState } from "react"

import { HelpButton } from "@/components/HelpButton"
import { Button } from "@/components/ui/button"
import { Dialog } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useI18n } from "@/i18n/context"
import { loadKeysStatus, saveKeys } from "@/lib/api"

type Props = {
  open: boolean
  onClose: () => void
  onSaved: () => void
}

export function KeysDialog({ open, onClose, onSaved }: Props) {
  const { messages } = useI18n()
  const t = messages.keys
  const [llmEnv, setLlmEnv] = useState("")
  const [llmField, setLlmField] = useState("deepseek_api_key")
  const [llmKey, setLlmKey] = useState("")
  const [hfKey, setHfKey] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (!open) {
      return
    }
    setLlmKey("")
    setHfKey("")
    setError(null)
    loadKeysStatus()
      .then((status) => {
        setLlmEnv(status.llm_env_var)
        setLlmField(status.llm_key_field)
      })
      .catch((err: Error) => setError(err.message))
  }, [open])

  async function apply(patch: Record<string, string | undefined>) {
    setBusy(true)
    setError(null)
    try {
      await saveKeys(patch)
      onSaved()
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed")
    } finally {
      setBusy(false)
    }
  }

  return (
    <Dialog open={open} onClose={onClose} title={t.title} className="w-[min(100%,32rem)]">
      <div className="flex items-start justify-between gap-2">
        <p>{t.intro}</p>
        <HelpButton helpKey="keys" />
      </div>
      <div className="mt-4 space-y-4">
        <div className="space-y-2">
          <Label htmlFor="llm-key">{t.llmLabel}</Label>
          <p className="text-xs text-muted-foreground">
            {t.llmHint} <code className="rounded bg-muted px-1">{llmEnv || "…"}</code>
          </p>
          <Input
            id="llm-key"
            type="password"
            autoComplete="off"
            placeholder="••••••••"
            value={llmKey}
            onChange={(event) => setLlmKey(event.target.value)}
          />
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={busy}
            onClick={() => void apply({ [llmField]: "" })}
          >
            {t.clearLlm}
          </Button>
        </div>
        <div className="space-y-2">
          <Label htmlFor="hf-key">{t.hfLabel}</Label>
          <p className="text-xs text-muted-foreground">{t.hfHint}</p>
          <Input
            id="hf-key"
            type="password"
            autoComplete="off"
            placeholder="••••••••"
            value={hfKey}
            onChange={(event) => setHfKey(event.target.value)}
          />
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={busy}
            onClick={() => void apply({ huggingface_api_key: "" })}
          >
            {t.clearHf}
          </Button>
        </div>
        {error ? <p className="text-sm text-destructive">{error}</p> : null}
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" onClick={onClose} disabled={busy}>
            {messages.common.cancel}
          </Button>
          <Button
            type="button"
            disabled={busy || (!llmKey && !hfKey)}
            onClick={() => {
              const patch: Record<string, string> = {}
              if (llmKey) {
                patch[llmField] = llmKey
              }
              if (hfKey) {
                patch.huggingface_api_key = hfKey
              }
              void apply(patch)
            }}
          >
            {messages.common.save}
          </Button>
        </div>
      </div>
    </Dialog>
  )
}
