# Question schema

## Purpose

Let the user define the variables to extract, and refuse a schema that cannot be applied.

## Requirements

### Requirement: Saved schema required
The system SHALL apply only a schema the user has explicitly saved. Draft edits MUST NOT change a schema already saved until the user saves again.

#### Scenario: Unsaved drafts
- **WHEN** the user has typed questions but has not saved the schema
- **THEN** the run control stays disabled
- **AND** the interface says that PDFs and a saved schema are both required

#### Scenario: Save succeeds
- **WHEN** the user saves one or more valid questions
- **THEN** the schema is kept for the current UI session
- **AND** the interface confirms how many questions were saved

### Requirement: Question shape
Each question MUST have a non-empty label, a non-empty question text, and one type: extraction, calculation, classification, or explanation. A classification question MUST have at least two categories, each with a code and a label. Any other type MUST NOT have categories.

#### Scenario: Classification with fewer than two categories
- **WHEN** the user saves a classification question with fewer than two complete categories
- **THEN** the schema is not saved
- **AND** the interface shows which question failed

#### Scenario: Categories on a non-classification question
- **WHEN** the user saves an extraction, calculation, or explanation question that includes categories
- **THEN** the schema is not saved

#### Scenario: Valid extraction question
- **WHEN** the user saves an extraction question with a label and question text and no categories
- **THEN** the schema is saved

### Requirement: Optional hints
A question MAY include an output-format hint and extra notes. When notes are present, they MUST be given to the model as additional rules for that question only. When an output-format hint is present, it MUST be given to the model for that question only.

#### Scenario: Notes on one question
- **WHEN** a saved question includes notes
- **THEN** those notes apply only to that question
- **AND** they do not change the rules of the other questions

#### Scenario: Output format on one question
- **WHEN** a saved question includes an output format
- **THEN** that hint is included in the prompt for that question
- **AND** a question without an output format does not receive that hint

### Requirement: Schema lifetime
Drafts MAY live only in the browser until save. The saved schema MUST live on the server session. It MUST NOT be written to disk or to `localStorage`.

#### Scenario: Reset
- **WHEN** the user resets outside a running pipeline
- **THEN** the saved schema remains
- **AND** previous results are cleared

#### Scenario: New UI session
- **WHEN** the user starts a new UI session
- **THEN** no previously saved schema is restored
