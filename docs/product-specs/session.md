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
The system SHALL drop the in-memory search index when the process exits. It MUST NOT require a database to recover that index.

#### Scenario: Process restart
- **WHEN** the process restarts
- **THEN** previously indexed documents are gone
- **AND** the user must upload them again to ask questions

### Requirement: Parser tier
The parser tier is a preference of the current session. The default is medium. Reset MUST keep the selected tier. Two sessions MAY select different tiers. A stored user profile MUST persist this same field for that user. The mapping from tier to method is not a per-user setting.

#### Scenario: Reset keeps the tier
- **WHEN** the user has selected a tier and then resets
- **THEN** the selected tier stays

#### Scenario: Two sessions
- **WHEN** two sessions have selected different tiers
- **THEN** each run uses the tier stored on its own session

### Requirement: No case text in the repository
The application MUST NOT write uploaded PDFs or API keys into the git repository.

#### Scenario: Normal run
- **WHEN** the user uploads a PDF and runs the pipeline
- **THEN** the PDF stays in a temporary directory for that session
- **AND** the application does not add the PDF or an API key to the repository
