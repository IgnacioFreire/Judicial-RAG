# Session

## Purpose

Keep one person's uploads and search index away from everyone else's, and drop them when the session ends.

## Requirements

### Requirement: Session isolation
The system MUST give each UI session its own upload directory and its own search index. A query MUST NOT return text stored for a different session.

#### Scenario: Two sessions
- **WHEN** two sessions have each uploaded a PDF
- **THEN** a question in one session is answered only from that session's index

### Requirement: Session lifetime
The system MUST delete a session's uploads and search index once the configured timeout has elapsed since that session was created, even if the session is still in use. The default timeout is 60 minutes. The clock MUST start at creation, not at the last interaction.

#### Scenario: Still in use at the timeout
- **WHEN** the configured timeout has passed since the session was created
- **THEN** the next UI load deletes that session's uploads and index

### Requirement: Process exit
The system MUST keep the search index in Supabase when the process exits. Uploaded PDFs MUST still be removed when the process exits. On each UI load the system MUST delete index rows that this process no longer tracks once they are older than the configured timeout, measured from when each row was first stored. A session this process still tracks MUST still be deleted from its creation time, as the session-lifetime requirement says.

#### Scenario: Restart within the timeout
- **WHEN** the process restarts and the UI loads before the timeout measured from when the rows were stored
- **THEN** those index rows are still stored
- **AND** the previous PDFs are not on disk

#### Scenario: Restart after the timeout
- **WHEN** the process restarts and the UI loads after that timeout
- **THEN** those index rows are deleted

### Requirement: Session preferences
The parser tier, the chunk tier, and the retrieval tier are preferences of the current session. Parser and chunk default to medium. Retrieval defaults to fast. Reset MUST keep all three. Two sessions MAY select different tiers. A stored user profile MUST persist these same fields for that user. The mapping from tier to method is not a per-user setting. The methods themselves are specified in [`document-upload.md`](document-upload.md), [`chunking.md`](chunking.md), and [`retrieval.md`](retrieval.md).

#### Scenario: Reset keeps the tier
- **WHEN** the user has selected a tier and then resets
- **THEN** the selected tier stays

#### Scenario: Two sessions
- **WHEN** two sessions have selected different tiers
- **THEN** each run uses the tier stored on its own session

### Requirement: No case text in the repository
The application MUST NOT write uploaded PDFs, chunk text, or API keys into the git repository. Chunk text and embeddings for a session MUST be stored in Supabase under that session id.

#### Scenario: Normal run
- **WHEN** the user uploads a PDF and runs the pipeline
- **THEN** the PDF stays in a temporary directory for that session
- **AND** the chunk text and embeddings are stored in Supabase under that session id
- **AND** the application does not add the PDF or an API key to the repository
