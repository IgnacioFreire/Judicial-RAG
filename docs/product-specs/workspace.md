# Workspace

## Purpose

Let a person see the session at a glance, follow each PDF, and edit questions away from the results.

Upload rules, schema rules, and answer rows stay in their own specs. This file only adds the screens and the session document list.

## Requirements

### Requirement: Routes
The UI SHALL provide an overview, a document list, a document detail, and a settings page. Settings SHALL hold the question editor and the parser, chunk, and retrieval tiers. The overview SHALL show the summary and the run controls.

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
The profile popover SHALL show the Supabase account email this process uses, the provider and model names, whether the active keys are set, and this session's generation token totals. It MUST NOT show key material.

#### Scenario: Key is set
- **WHEN** the active LLM key is present in the server settings
- **THEN** the profile says the key is configured
- **AND** the key value is not in the response

### Requirement: New session
A new UI session SHALL NOT restore another session's rows, answers, or token totals.
