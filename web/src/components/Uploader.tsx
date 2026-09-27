import type { ChangeEvent, RefObject } from "react"
import { FileUp } from "lucide-react"

import { Alert } from "@/components/ui/alert"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { saveUploads } from "@/lib/api"
import { fieldClass } from "@/lib/styles"

type Props = {
  files: string[]
  rejected: string[]
  emptyHint: boolean
  disabled: boolean
  maxMb: number
  onChange: (accepted: string[], rejected: string[]) => void
  fileRef: RefObject<HTMLInputElement | null>
}

export function Uploader({
  files,
  rejected,
  emptyHint,
  disabled,
  maxMb,
  onChange,
  fileRef,
}: Props) {
  async function handleChange(event: ChangeEvent<HTMLInputElement>) {
    const selected = Array.from(event.target.files ?? [])
    const result = await saveUploads(selected)
    onChange(
      result.accepted_files,
      result.rejected.map((row) => row.detail),
    )
  }

  return (
    <section className="space-y-3">
      <div className="flex items-center gap-2 text-foreground">
        <FileUp className="size-4 text-muted-foreground" />
        <h2 className="text-sm font-semibold">Upload documents</h2>
      </div>
      <Label htmlFor="pdfs" className="text-muted-foreground">
        Upload one or more PDF files
      </Label>
      <Input
        id="pdfs"
        ref={fileRef}
        type="file"
        accept=".pdf,application/pdf"
        multiple
        disabled={disabled}
        className={`${fieldClass} file:mr-3 file:rounded-lg file:border-0 file:bg-muted file:px-2 file:py-1 file:text-foreground`}
        onChange={handleChange}
      />
      <p className="text-xs text-muted-foreground">Maximum {maxMb} MB per file.</p>
      {emptyHint && files.length === 0 ? (
        <Alert className="border-border bg-muted text-muted-foreground">
          Upload at least one PDF to get started.
        </Alert>
      ) : null}
      {rejected.length > 0 ? (
        <Alert className="border-red-900/60 bg-red-950/40 text-red-200">
          Files rejected (size limit exceeded):
          <ul className="mt-1 list-disc pl-4">
            {rejected.map((row) => (
              <li key={row}>{row}</li>
            ))}
          </ul>
        </Alert>
      ) : null}
      {files.length > 0 ? (
        <Alert className="border-emerald-900/50 bg-emerald-950/30 text-emerald-200">
          {files.length} file(s) ready: {files.join(", ")}
        </Alert>
      ) : null}
    </section>
  )
}
