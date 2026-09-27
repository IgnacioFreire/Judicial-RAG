import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { darkField, darkTextarea } from "@/lib/styles"
import { TYPE_OPTIONS, type QuestionDraft, type QuestionType } from "@/lib/types"

type Props = {
  draft: QuestionDraft
  index: number
  disabled: boolean
  onChange: (draft: QuestionDraft) => void
  onRemove: () => void
}

export function QuestionEditor({ draft, index, disabled, onChange, onRemove }: Props) {
  const title = draft.label || `Question ${index + 1}`

  return (
    <details
      open={draft.expanded}
      className="rounded-2xl border border-zinc-800 bg-zinc-950 p-3"
    >
      <summary className="cursor-pointer text-sm font-medium text-zinc-100">{title}</summary>
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <div className="space-y-1">
          <Label className="text-zinc-400">Label</Label>
          <Input
            className={darkField}
            value={draft.label}
            placeholder="e.g. Sentencing date"
            disabled={disabled}
            onChange={(event) => onChange({ ...draft, label: event.target.value })}
          />
        </div>
        <div className="space-y-1">
          <Label className="text-zinc-400">Type</Label>
          <select
            className={darkField}
            value={draft.question_type}
            disabled={disabled}
            onChange={(event) =>
              onChange({
                ...draft,
                question_type: event.target.value as QuestionType,
              })
            }
          >
            {TYPE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-1 sm:col-span-2">
          <Label className="text-zinc-400">Question / extraction rule</Label>
          <Textarea
            className={darkTextarea}
            value={draft.question}
            placeholder="e.g. What is the date of the sentence? Format: DD/MM/YYYY"
            disabled={disabled}
            onChange={(event) => onChange({ ...draft, question: event.target.value })}
          />
        </div>
        <div className="space-y-1">
          <Label className="text-zinc-400">Expected output format (optional)</Label>
          <Input
            className={darkField}
            value={draft.output_format}
            placeholder="e.g. DD/MM/YYYY, integer"
            disabled={disabled}
            onChange={(event) =>
              onChange({ ...draft, output_format: event.target.value })
            }
          />
        </div>
        <div className="space-y-1">
          <Label className="text-zinc-400">Additional rules (optional)</Label>
          <Input
            className={darkField}
            value={draft.notes}
            placeholder="e.g. Round to nearest integer"
            disabled={disabled}
            onChange={(event) => onChange({ ...draft, notes: event.target.value })}
          />
        </div>
      </div>
      {draft.question_type === "classification" ? (
        <div className="mt-3 space-y-2">
          <p className="text-sm font-semibold text-zinc-200">Categories</p>
          {draft.categories.map((category) => (
            <div key={category.id} className="grid grid-cols-[1fr_3fr_auto] gap-2">
              <Input
                className={darkField}
                value={category.code}
                placeholder="1"
                disabled={disabled}
                onChange={(event) =>
                  onChange({
                    ...draft,
                    categories: draft.categories.map((row) =>
                      row.id === category.id
                        ? { ...row, code: event.target.value }
                        : row,
                    ),
                  })
                }
              />
              <Input
                className={darkField}
                value={category.label}
                placeholder="Conviction"
                disabled={disabled}
                onChange={(event) =>
                  onChange({
                    ...draft,
                    categories: draft.categories.map((row) =>
                      row.id === category.id
                        ? { ...row, label: event.target.value }
                        : row,
                    ),
                  })
                }
              />
              <Button
                type="button"
                variant="sidebar"
                disabled={disabled}
                onClick={() =>
                  onChange({
                    ...draft,
                    categories: draft.categories.filter((row) => row.id !== category.id),
                  })
                }
              >
                ✕
              </Button>
            </div>
          ))}
          <Button
            type="button"
            variant="sidebar"
            size="sm"
            disabled={disabled}
            onClick={() =>
              onChange({
                ...draft,
                categories: [
                  ...draft.categories,
                  { id: crypto.randomUUID(), code: "", label: "" },
                ],
              })
            }
          >
            Add category
          </Button>
        </div>
      ) : null}
      <Button
        type="button"
        variant="sidebar"
        className="mt-3"
        disabled={disabled}
        onClick={onRemove}
      >
        Remove question
      </Button>
    </details>
  )
}
