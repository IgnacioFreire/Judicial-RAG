"""Tests for prompt construction and response parsing in the RAG agent.

The fragments below are synthetic. They are not rulings.
"""

import logging

from models.query import QuestionType, UserQuestion
from pipeline.rag_agent import _build_prompt, _parse_response


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


def _chunks() -> list[dict]:
    return [
        {
            "text": "synthetic fragment",
            "page": 2,
            "headings": [],
            "distance": 0.25,
        }
    ]


def test_markdown_fence_and_surrounding_text_are_parsed() -> None:
    payload = (
        '{"answer": "01/02/2020", "confidence": "high", '
        '"answer_source": "direct", "citation": "synthetic fragment"}'
    )
    fenced = f"```json\n{payload}\n```"
    surrounded = (
        "Here is the object:\n"
        '{"answer": "01/02/2020", "confidence": "medium", '
        '"answer_source": "inferred", "citation": null}'
    )
    question = _question()

    fenced_answer = _parse_response(fenced, question, "a.pdf", _chunks())
    surrounded_answer = _parse_response(surrounded, question, "a.pdf", _chunks())

    assert fenced_answer.answer == "01/02/2020"
    assert fenced_answer.confidence.value == "high"
    assert fenced_answer.citation is not None
    assert fenced_answer.citation.page == 2
    assert surrounded_answer.confidence.value == "medium"
    assert surrounded_answer.citation is None


def test_non_json_response_is_not_found_and_is_not_logged(caplog) -> None:
    marker = "SYNTHETIC_RESPONSE_BODY"
    with caplog.at_level(logging.WARNING):
        answer = _parse_response(marker, _question(), "a.pdf", _chunks())

    assert answer.confidence.value == "not_found"
    assert answer.answer is None
    assert marker not in caplog.text
