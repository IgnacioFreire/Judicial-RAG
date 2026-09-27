# Chunking

## Purpose

Split each extracted PDF into chunks before they are embedded. The page of each chunk stays on the chunk so a citation can name it.

## Requirements

### Requirement: Chunk tier
The system SHALL chunk each accepted PDF with the chunk tier selected in advanced settings. The tiers are `fast`, `medium`, and `slow`. `config/chunkers.py` maps them to window, hybrid, and context. The default tier is medium. Window size is 512 tokens of the embedding tokenizer.

#### Scenario: Default chunk tier
- **WHEN** the user has not changed the chunking setting
- **THEN** a Docling extraction uses the section chunker at 512 tokens of the embedding tokenizer
- **AND** the heading is stored on the chunk and inside the stored text

#### Scenario: Fast chunk tier
- **WHEN** the user selects the fast chunk tier
- **THEN** each page is cut into 512-token windows of that tokenizer
- **AND** a short page stays one chunk
- **AND** the page number on every window is the page it came from

#### Scenario: Slow chunk tier
- **WHEN** the user selects the slow chunk tier
- **THEN** the chunks are the same section chunks as the medium tier
- **AND** at embed time one situation sentence from the configured LLM is prepended to the text sent to the embedding model
- **AND** the text stored for the citation stays the chunk without that sentence

Parser choice is specified in [`document-upload.md`](document-upload.md). How a question finds chunks is specified in [`retrieval.md`](retrieval.md).
