import type { QuestionDraft, RunEvent, SessionView } from "@/lib/types"

const jsonHeaders = { "Content-Type": "application/json" }

async function parse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as { detail?: string }
    throw new Error(body.detail ?? response.statusText)
  }
  return (await response.json()) as T
}

export function loadSession(): Promise<SessionView> {
  return fetch("/api/session", { credentials: "include" }).then((r) =>
    parse<SessionView>(r),
  )
}

export function saveUploads(files: File[]): Promise<{
  accepted_files: string[]
  rejected: { name: string; detail: string }[]
}> {
  const body = new FormData()
  for (const file of files) {
    body.append("files", file)
  }
  return fetch("/api/uploads", {
    method: "PUT",
    credentials: "include",
    body,
  }).then((r) => parse(r))
}

export function saveSchema(drafts: QuestionDraft[]): Promise<{
  saved: boolean
  question_count: number
  error: { message: string; question_index: number | null } | null
}> {
  const payload = drafts.map((draft) => ({
    label: draft.label,
    question: draft.question,
    question_type: draft.question_type,
    output_format: draft.output_format,
    notes: draft.notes,
    categories: draft.categories.map((row) => ({
      code: row.code,
      label: row.label,
    })),
  }))
  return fetch("/api/schema", {
    method: "PUT",
    credentials: "include",
    headers: jsonHeaders,
    body: JSON.stringify(payload),
  }).then((r) => parse(r))
}

export function saveTiers(body: {
  parser_tier?: string
  chunk_tier?: string
  embedding_tier?: string
}): Promise<SessionView> {
  return fetch("/api/session/tiers", {
    method: "PATCH",
    credentials: "include",
    headers: jsonHeaders,
    body: JSON.stringify(body),
  }).then((r) => parse<SessionView>(r))
}

export function resetSession(): Promise<SessionView> {
  return fetch("/api/reset", { method: "POST", credentials: "include" }).then((r) =>
    parse<SessionView>(r),
  )
}

export async function runPipeline(onEvent: (event: RunEvent) => void): Promise<void> {
  const response = await fetch("/api/run", {
    method: "POST",
    credentials: "include",
  })
  if (!response.ok || !response.body) {
    const body = (await response.json().catch(() => ({}))) as { detail?: string }
    throw new Error(body.detail ?? "Run failed")
  }
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""
  while (true) {
    const { done, value } = await reader.read()
    buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done })
    const chunks = buffer.split("\n\n")
    buffer = chunks.pop() ?? ""
    for (const chunk of chunks) {
      for (const line of chunk.split("\n")) {
        if (!line.startsWith("data: ")) {
          continue
        }
        onEvent(JSON.parse(line.slice(6)) as RunEvent)
      }
    }
    if (done) {
      break
    }
  }
}
