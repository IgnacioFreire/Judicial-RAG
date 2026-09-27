# Workspace

## Purpose

Let a person see the session at a glance, follow each PDF, and edit questions away from the results.

Upload rules, schema rules, and answer rows stay in their own specs. This file only adds the screens and the session document list.

## Requirements

### Requirement: Routes
The UI SHALL provide an overview, a document list, a document detail, and a settings page. Settings SHALL hold the question editor and the parser, chunk, and retrieval tiers. The overview SHALL show the summary and the run controls.

### Requirement: Overview composition
The overview SHALL show the accepted PDF count, whether the schema is saved, the question count, and the answered ratio when a run has results. It SHALL also show a recent document list and links to the document upload page and to the question editor.

#### Scenario: Empty session
- **WHEN** the user opens the overview with no accepted PDFs
- **THEN** the recent list is empty
- **AND** the next-step links still open documents and settings

#### Scenario: Open settings
- **WHEN** the user opens settings
- **THEN** the question editor and the three tiers are on that page
- **AND** the shared instruction text in the pipeline is not editable there

### Requirement: Document list
The document list SHALL show each PDF accepted in the current session with a status of ready, queued, extracting, embedding, answering, done, or failed, and the accepted and finished times once those events have happened.

#### Scenario: Accepted before a run
- **WHEN** the user accepts a PDF and has not run
- **THEN** that row is ready

#### Scenario: One file fails and another finishes
- **WHEN** a run indexes one PDF and reports an error for another
- **THEN** the indexed PDF is done
- **AND** the failed PDF is failed and is not an answered document

### Requirement: Document detail
Opening a done document SHALL show that document's answers only. A ready or failed document SHALL show no answer list.

#### Scenario: Other session
- **WHEN** a request names a PDF that is not in the current session
- **THEN** the response is not found

### Requirement: Reset
Reset SHALL clear the document list, its times, and the session token totals. It SHALL keep the saved schema and the three tiers.

### Requirement: Profile
The profile popover SHALL show the Supabase account email this process uses, the provider and model names, whether the active keys are set, and this session's generation token totals. It MUST NOT show key material. The popover SHALL offer sign out, a keys dialog, theme, and language controls.

#### Scenario: Key is set
- **WHEN** the active LLM key is present in the server settings or in this session's key overrides
- **THEN** the profile says the key is configured
- **AND** the key value is not in the response

### Requirement: Sign out
Sign out SHALL end the current browser session: delete its uploads, index rows, UI state, and token totals, then issue a new session cookie. Theme and language choices stored in the browser SHALL remain.

#### Scenario: Sign out while idle
- **WHEN** the user signs out and no run is in progress
- **THEN** the next request uses a new session with empty documents and results

#### Scenario: Sign out during a run
- **WHEN** the user signs out while a run is in progress
- **THEN** the response is conflict

### Requirement: Session API keys
The keys dialog SHALL let the user set optional overrides for the active LLM provider key and the Hugging Face embedding key for this session only. Saving SHALL not return key values. Clearing an override SHALL fall back to the server environment keys.

#### Scenario: Override for a run
- **WHEN** the user saves a session LLM key override and runs the pipeline
- **THEN** generation calls use the override for that session

### Requirement: Theme
The UI SHALL support light and dark themes. The choice SHALL persist in the browser and apply to every route.

### Requirement: Locale
The UI SHALL support English and Spanish. The choice SHALL persist in the browser. Pipeline-facing type names and API enums stay as in the code.

### Requirement: Contextual help
Pages and major controls SHALL offer a help control that opens a short explanation dialog. Help text SHALL follow the active locale.

### Requirement: New session
A new UI session SHALL NOT restore another session's rows, answers, or token totals.
