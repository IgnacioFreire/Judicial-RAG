"""Tests for prompt construction in the RAG agent.

The fragments below are synthetic. They are not rulings.
"""

from models.query import QuestionType, UserQuestion
from pipeline.rag_agent import _build_prompt


def _question(**overrides: object) -> UserQuestion:
    data: dict = {
        "label": "When",
        "question": "What date is stated?",
        "question_type": QuestionType.EXTRACTION,
    }
    data.update(overrides)
    return UserQuestion(**data)


def test_output_format_is_included_for_that_question_only() -> None:
    chunks = [
        {
            "text": "synthetic fragment",
            "page": 1,
            "headings": [],
            "distance": 0.1,
        }
    ]
    with_format = _build_prompt(_question(output_format="DD/MM/YYYY"), chunks)
    without_format = _build_prompt(_question(), chunks)

    assert "DD/MM/YYYY" in with_format
    assert "Expected output format" in with_format
    assert "DD/MM/YYYY" not in without_format
    assert "Expected output format" not in without_format
