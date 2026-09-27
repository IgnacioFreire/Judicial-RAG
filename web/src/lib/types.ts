export type QuestionType =
  | "extraction"
  | "calculation"
  | "classification"
  | "explanation"

export type CategoryDraft = {
  id: string
  code: string
  label: string
}

export type QuestionDraft = {
  id: string
  label: string
  question: string
  question_type: QuestionType
  output_format: string
  notes: string
  categories: CategoryDraft[]
  expanded: boolean
}

export type TierOption = {
  value: string
  label: string
}

export type SessionView = {
  parser_tier: string
  chunk_tier: string
  embedding_tier: string
  parser_options: TierOption[]
  chunk_options: TierOption[]
  embedding_options: TierOption[]
  accepted_files: string[]
  schema_saved: boolean
  question_count: number
  is_processing: boolean
  run_errors: string[]
  pipeline_error: string | null
  success_message: string | null
  results: DocumentAnswers[] | null
  max_upload_mb: number
}

export type DocumentRow = {
  name: string
  status: string
  accepted_at: string
  started_at: string | null
  finished_at: string | null
}

export type DocumentDetail = DocumentRow & {
  answers: DocumentAnswers | null
}

export type ProfileView = {
  email: string
  llm_provider: string
  llm_model: string
  llm_key_configured: boolean
  embedding_provider: string
  embedding_model: string
  huggingface_key_configured: boolean
  input_tokens: number
  output_tokens: number
}

export type KeysView = {
  llm_key_configured: boolean
  huggingface_key_configured: boolean
  llm_env_var: string
  llm_key_field: string
  huggingface_env_var: string
}

export type DocumentAnswers = {
  document: string
  answers: AgentAnswer[]
}

export type AgentAnswer = {
  question: { label: string }
  answer: string | null
  citation: { text: string; page: number; score: number } | null
  document: string
  confidence: "high" | "medium" | "low" | "not_found"
  answer_source: "direct" | "inferred" | null
}

export type RunEvent = {
  type: "progress" | "done" | "failed"
  stage: string
  source: string
  message: string
  current: number
  total: number
  results: DocumentAnswers[] | null
}

export const TYPE_OPTIONS: { value: QuestionType; label: string }[] = [
  {
    value: "extraction",
    label: "Extraction — copy a value directly from the text",
  },
  {
    value: "calculation",
    label: "Calculation — derive a value from extracted data",
  },
  {
    value: "classification",
    label: "Classification — assign to a category from a list",
  },
  {
    value: "explanation",
    label: "Explanation — explain why or how something happened",
  },
]
