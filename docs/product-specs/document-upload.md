# Document upload

## Purpose

Accept the PDFs a person wants read in this session, and refuse files the pipeline should not open.

## Requirements

### Requirement: PDF upload
The system SHALL accept one or more PDF files for the current session and SHALL make each accepted file available to a later run.

#### Scenario: One or more PDFs
- **WHEN** the user uploads one or more PDF files within the size limit
- **THEN** each file is kept for the current session
- **AND** the interface reports how many files are ready

### Requirement: Size limit
The system MUST reject a PDF larger than 20 MB and MUST still accept the other files in the same upload.

#### Scenario: Mixed sizes
- **WHEN** the user uploads one PDF over 20 MB and one PDF at or under 20 MB
- **THEN** the oversized file is rejected with its name and size
- **AND** the smaller PDF stays available to run

### Requirement: Empty upload
The system SHALL NOT offer a pipeline run when no PDF has been accepted.

#### Scenario: Nothing uploaded
- **WHEN** the user has not uploaded an accepted PDF
- **THEN** the run control stays disabled
- **AND** the interface tells the user to upload at least one PDF

### Requirement: Parser tier
The system SHALL extract each accepted PDF with the parser tier selected in advanced settings. The tiers are `fast`, `medium`, and `slow`. `config/parsers.py` maps them to pymupdf4llm, docling, and marker. The default tier is medium. The system MUST NOT ask the user whether the PDF is scanned.

#### Scenario: Default tier
- **WHEN** the user has not changed advanced settings
- **AND** the user runs the pipeline on an accepted PDF
- **THEN** extraction uses docling on the digital text layer
- **AND** OCR stays off

#### Scenario: Fast tier
- **WHEN** the user selects the fast parser tier
- **THEN** extraction uses pymupdf4llm on the digital text layer

#### Scenario: Slow tier
- **WHEN** the user selects the slow tier
- **THEN** extraction uses marker
- **AND** marker may OCR a region that has no usable text layer

How the extracted text is split is specified in [`chunking.md`](chunking.md).

### Requirement: Same file name
The system MUST replace the stored bytes when an accepted upload uses a name already stored in the session.

#### Scenario: Second upload with the same name
- **WHEN** the user uploads a PDF whose name matches a file already stored
- **THEN** a later run reads the new bytes

### Requirement: File removed from the uploader
The system MUST delete a PDF that is no longer in the uploader from the session directory. The next run MUST NOT answer it.

#### Scenario: One of two files removed
- **WHEN** the user had two accepted PDFs and removes one from the uploader
- **THEN** the removed file is deleted from the session directory
- **AND** the next run answers only the PDF that remains
