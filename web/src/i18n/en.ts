export const en = {
  app: {
    name: "Judicial RAG",
    tagline: "Extract and classify variables from judicial PDF documents.",
    workspace: "Workspace",
  },
  nav: {
    overview: "Overview",
    documents: "Documents",
    settings: "Settings",
  },
  common: {
    loading: "Loading…",
    configured: "Configured",
    missing: "Missing",
    cancel: "Cancel",
    save: "Save",
    close: "Close",
    notSet: "Not set",
    dash: "—",
  },
  theme: {
    light: "Light",
    dark: "Dark",
  },
  locale: {
    en: "English",
    es: "Español",
  },
  profile: {
    title: "Profile",
    account: "Supabase account",
    llm: "LLM",
    activeLlmKey: "Active LLM key",
    embeddings: "Embeddings",
    hfKey: "Hugging Face key",
    tokens: "Generation tokens",
    tokensHint: "This session only. Embedding calls are not included.",
    signOut: "Sign out",
    keys: "API keys",
    theme: "Theme",
    language: "Language",
  },
  keys: {
    title: "Session API keys",
    intro:
      "Optional overrides for this browser session only. Values are never shown again after saving. Server environment keys are used when a field is empty.",
    llmLabel: "LLM key",
    llmHint: "Environment variable for the active provider:",
    hfLabel: "Hugging Face key",
    hfHint: "Used for embedding calls when retrieval is enabled.",
    clearLlm: "Clear LLM override",
    clearHf: "Clear Hugging Face override",
    saved: "Keys updated.",
  },
  run: {
    run: "Run pipeline",
    reset: "Reset",
    hint: "Upload PDFs and save a schema first.",
  },
  overview: {
    title: "Overview",
    documents: "Documents",
    documentsHint: "PDFs in this session",
    schema: "Schema",
    saved: "Saved",
    draft: "Draft",
    schemaSavedHint: "question(s)",
    schemaDraftHint: "Save schema to run",
    questions: "Questions",
    questionsHint: "On the saved schema",
    answered: "Answered",
    answeredHint: "Rows that are not not_found",
    recent: "Recent documents",
    noDocuments: "No PDFs in this session yet.",
    nextTitle: "Next steps",
    nextUpload: "Upload PDFs",
    nextUploadHint: "Add files on the documents page.",
    nextSchema: "Define questions",
    nextSchemaHint: "Save a schema before you run.",
    viewAll: "View all",
  },
  documents: {
    title: "Documents",
    subtitle: "Accepted PDFs in this session, with status and times.",
    name: "Name",
    status: "Status",
    accepted: "Accepted",
    finished: "Finished",
    empty: "No PDFs in this session yet.",
    count: "in this session",
  },
  documentDetail: {
    back: "Documents",
    notFound: "Document not found.",
    backLink: "Back to documents",
    finished: "finished",
    accepted: "accepted",
    answers: "Answers",
    noAnswers: "No answers yet for this document.",
  },
  settings: {
    title: "Settings",
    subtitle: "Questions, save schema, and the three session tiers.",
    typesTitle: "Question types",
    typesIntro:
      "Each type uses the instruction in pipeline/rag_agent.py. The editable text is the question, the output format, and the notes.",
  },
  help: {
    overview: {
      title: "Overview",
      body:
        "Summary of this session: how many PDFs are accepted, whether a schema is saved, and how many answers were found. Use Run pipeline after upload and save. Reset clears PDFs and results but keeps your schema and tiers.",
    },
    documents: {
      title: "Documents",
      body:
        "Upload PDFs here and track each file from ready through extracting, embedding, answering, done, or failed. Open a row to see answers when the run finished that file.",
    },
    documentDetail: {
      title: "Document detail",
      body:
        "Status and timestamps for one PDF. Answers and citations appear only when the pipeline completed that file successfully.",
    },
    settings: {
      title: "Settings",
      body:
        "Define questions and save the schema before running. Advanced settings choose parser, chunking, and retrieval speed. The shared agent instruction in the pipeline is not edited here.",
    },
    run: {
      title: "Run pipeline",
      body:
        "Processes every accepted PDF against the saved schema. Progress streams live; one failure does not stop other files.",
    },
    schema: {
      title: "Question schema",
      body:
        "Each row is one variable to extract. Save schema to persist it for runs. Drafts are lost on refresh until saved.",
    },
    tiers: {
      title: "Advanced tiers",
      body:
        "Parser, chunking, and retrieval tiers trade speed for quality. They apply to the next run in this session.",
    },
    profile: {
      title: "Profile",
      body:
        "Account email and models come from server configuration. Token counts are generation only for this session. Sign out ends the session and clears uploads.",
    },
    keys: {
      title: "API keys",
      body:
        "Session overrides are stored in memory on the server until sign-out or expiry. They are never returned in API responses.",
    },
  },
} as const

export type Messages = typeof en
