# Generated

This directory is for artifacts produced from code (a dumped schema, an inventory). They are not edited by hand.

There are none today. judicial-rag has no database. The data contract is the Pydantic models:

- `models/document.py` — `Chunk`, `DocumentMetadata`, `DocumentResult`
- `models/query.py` — `QuestionType`, `UserQuestion`, `QuestionSchema`, `AgentAnswer`, `DocumentAnswers`, `Citation`

Copying them here would lie as soon as a field changes. Read those modules.

When a generator exists, its output lands in this directory, the command that regenerates it is documented in this README, and the file is not hand-edited.
