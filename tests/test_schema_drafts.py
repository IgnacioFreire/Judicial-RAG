"""Tests for building a QuestionSchema from editor drafts."""

from app.schema_drafts import CategoryDraft, QuestionDraft, build_schema
from models.query import QuestionType


def test_valid_extraction_saves() -> None:
    schema, error = build_schema(
        [
            QuestionDraft(
                label="Date",
                question="What is the date?",
                question_type=QuestionType.EXTRACTION,
            )
        ]
    )
    assert error is None
    assert schema is not None
    assert len(schema.questions) == 1


def test_empty_list_is_rejected() -> None:
    schema, error = build_schema([])
    assert schema is None
    assert error is not None
    assert "at least one question" in error.message.lower()


def test_classification_needs_two_categories() -> None:
    schema, error = build_schema(
        [
            QuestionDraft(
                label="Type",
                question="What type?",
                question_type=QuestionType.CLASSIFICATION,
                categories=[CategoryDraft(code="1", label="One")],
            )
        ]
    )
    assert schema is None
    assert error is not None
    assert error.question_index == 0
