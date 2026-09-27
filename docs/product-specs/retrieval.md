# Retrieval

## Purpose

For one question and one PDF in the current session, return the fragments the agent will read.

## Requirements

### Requirement: Retrieval tier
The system SHALL retrieve fragments with the retrieval tier selected in advanced settings. The tiers are `fast`, `medium`, and `slow`. `config/embeddings.py` maps them to dense, hybrid, and rerank. The default tier is fast.

Fast returns the 5 closest chunks by cosine distance. Medium fuses a dense shortlist with a word search (BM25) and then returns 5. Slow fuses a few dozen candidates, reranks them with a cross-encoder, and then returns 5. Search is always filtered to one `session_id` and one PDF filename.

The citation score is `1 - distance` from the dense hit when that chunk was in the dense list. A chunk found only by words has distance 1. The page and the score shown with a citation still come from the highest-ranked fragment after this retrieval, as specified in [`variable-extraction.md`](variable-extraction.md).

#### Scenario: Default retrieval
- **WHEN** the user has not changed the retrieval setting
- **THEN** search uses the vector only
- **AND** five chunks are returned, lowest cosine distance first

#### Scenario: Word search
- **WHEN** the user selects the medium retrieval tier
- **THEN** a chunk that contains a rare word from the question can outrank a closer vector that does not contain it

#### Scenario: Rerank
- **WHEN** the user selects the slow retrieval tier
- **THEN** a cross-encoder reorders the fused candidates before the five chunks are returned
