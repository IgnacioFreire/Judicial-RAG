# Variable extraction

## Purpose

For every indexed document and every saved question, return one answer with a confidence and, when the text supports it, a citation from that same document.

## Requirements

### Requirement: One row per question
The system SHALL return one answer for every saved question on every document that was indexed. A missing or failed answer MUST still occupy that row.

#### Scenario: Value found
- **WHEN** the indexed document contains the requested value
- **THEN** the row includes the answer text, a confidence of high, medium, or low, and whether the answer was copied or inferred

#### Scenario: Value absent or the model call fails
- **WHEN** the document has no relevant text, the model call fails, or the model response is not valid JSON
- **THEN** that row has confidence not_found
- **AND** the other questions for that document are still answered

### Requirement: Question types
The system MUST instruct the model according to the saved question type. Extraction SHALL be requested as a verbatim copy marked direct. Calculation SHALL be requested as a derived value marked inferred. Classification SHALL be requested as exactly one category code from that question's list, marked direct when the text states the category and inferred when the match is implicit. Explanation SHALL be requested in Spanish and marked inferred. The system does not check that the model obeyed the type after the call returns.

#### Scenario: Classification question
- **WHEN** the user runs a classification question against an indexed document
- **THEN** the model is given that question's category codes and labels
- **AND** it is told to return one of those codes

#### Scenario: Explanation question
- **WHEN** the user runs an explanation question against an indexed document
- **THEN** the model is told to answer in Spanish
- **AND** it is told to mark the answer inferred

### Requirement: Citation
When the model names a supporting fragment, the system SHALL show that fragment with a page number and a similarity score between 0 and 1. The page and the score MUST come from the highest-ranked retrieved fragment for that question.

#### Scenario: Cited answer
- **WHEN** the model returns a citation string and at least one fragment was retrieved
- **THEN** the interface shows the citation text, a page, and a score
- **AND** the page is the page of the highest-ranked fragment, not a page chosen by searching the citation text

#### Scenario: No fragment retrieved
- **WHEN** retrieval returns no fragments for that question and document
- **THEN** the row is not_found
- **AND** no citation is shown

### Requirement: Document scope
The system MUST answer each question using only text from the document that row belongs to. Text from another uploaded PDF MUST NOT appear in that answer.

#### Scenario: Two PDFs in one run
- **WHEN** the user runs the same schema on two indexed PDFs
- **THEN** each document has its own set of answers
- **AND** a citation on one document names that document as its source

### Requirement: Batch failure isolation
The system SHALL keep processing the rest of a batch when one PDF fails to index. A PDF that fails MUST NOT appear as an answered document.

#### Scenario: One bad PDF
- **WHEN** one PDF fails during extraction or embedding and another PDF succeeds
- **THEN** the interface warns that the failed file was not processed
- **AND** the warning is still visible after the run finishes
- **AND** the successful PDF still receives an answer row per saved question

#### Scenario: PDF with no text
- **WHEN** extraction finishes but produces no text chunks
- **THEN** the interface warns that the file was not processed
- **AND** that PDF does not appear as an answered document

### Requirement: Current upload set
The system MUST answer only PDFs indexed successfully in the current run. A PDF indexed earlier and absent from this run's upload set MUST NOT be answered.

#### Scenario: Second run without one of the files
- **WHEN** a session has indexed two PDFs and the user runs again with only one of them
- **THEN** results contain only the PDF included in the second run

### Requirement: Run and progress
The system SHALL enable a run only when at least one PDF is accepted, a schema is saved, and no run is in progress. During a run it MUST show progress and MUST disable upload, schema edits, run, and reset.

#### Scenario: Ready to run
- **WHEN** an accepted PDF and a saved schema are both present and nothing is running
- **THEN** the run control is enabled

#### Scenario: Run in progress
- **WHEN** a run is in progress
- **THEN** upload, schema editing, run, and reset are disabled
- **AND** the interface shows the current stage

### Requirement: Results
The system SHALL group results by document and SHALL show, per question, the label, the confidence, the answer or a not-found caption, whether the answer was direct or inferred, and the citation when one exists.

#### Scenario: Finished run
- **WHEN** a run completes
- **THEN** each indexed document is listed with how many of its questions were answered
- **AND** a not_found row is shown as unanswered rather than omitted
