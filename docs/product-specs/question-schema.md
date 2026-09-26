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
A question MAY include an output-format hint and extra notes. When present, those notes MUST be given to the model as additional rules for that question only.

#### Scenario: Notes on one question
- **WHEN** a saved question includes notes
- **THEN** those notes apply only to that question
- **AND** they do not change the rules of the other questions

### Requirement: Schema lifetime
The system SHALL keep the saved schema in the current UI session only. It MUST NOT write the schema to disk.

#### Scenario: Reset
- **WHEN** the user resets outside a running pipeline
- **THEN** the saved schema remains
- **AND** previous results are cleared

#### Scenario: New UI session
- **WHEN** the user starts a new UI session
- **THEN** no previously saved schema is restored
